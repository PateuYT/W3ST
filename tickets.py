import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os

from utils.embeds import EmbedBuilder, PRIMARY_COLOR, SUCCESS_COLOR, WARNING_COLOR
from utils.database import TicketDatabase

db = TicketDatabase()

TICKET_TYPES = {
    'support': {
        'label': 'Support',
        'description': 'General help & assistance',
        'emoji': '🛠️',
        'color': PRIMARY_COLOR
    },
    'order': {
        'label': 'Order',
        'description': 'Purchase our services',
        'emoji': '🛒',
        'color': 0x22C55E
    },
    'staff': {
        'label': 'Staff Application',
        'description': 'Apply to join our team',
        'emoji': '👔',
        'color': 0x3B82F6
    },
    'refund': {
        'label': 'Refund',
        'description': 'Request a refund',
        'emoji': '💰',
        'color': 0xF59E0B
    }
}

class TicketTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=info['label'],
                description=info['description'],
                emoji=info['emoji'],
                value=key
            )
            for key, info in TICKET_TYPES.items()
        ]
        
        super().__init__(
            placeholder="Select ticket type...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_type_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Check blacklist
        if db.is_blacklisted(str(interaction.user.id)):
            await interaction.response.send_message(
                embed=EmbedBuilder.error("You are blacklisted from creating tickets!"),
                ephemeral=True
            )
            return
        
        # Check max tickets
        user_tickets = db.get_user_tickets(str(interaction.user.id))
        if len(user_tickets) >= 1:  # Max 1 ticket per user
            await interaction.response.send_message(
                embed=EmbedBuilder.error(f"You already have an open ticket! Close it first."),
                ephemeral=True
            )
            return
        
        await self.create_ticket(interaction, self.values[0])
    
    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        guild = interaction.guild
        user = interaction.user
        
        # Get config from environment or config
        category_id = 1473374359568781403
        staff_role_id = 1441463909155344576
        
        category = guild.get_channel(category_id)
        staff_role = guild.get_role(staff_role_id)
        
        if not category or not staff_role:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Configuration error. Contact admin."),
                ephemeral=True
            )
            return
        
        # Create channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        ticket_info = TICKET_TYPES[ticket_type]
        channel_name = f"ticket-{db.ticket_counter + 1:04d}"
        
        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"West Ticket | {user.name} | {ticket_info['label']}"
            )
            
            # Save to database
            ticket_id = db.create_ticket(str(user.id), str(channel.id), ticket_type)
            
            # Send welcome message
            embed = EmbedBuilder.ticket_welcome(ticket_type, {'id': ticket_id, **ticket_info}, user)
            view = TicketControlView(ticket_id)
            
            await channel.send(f"{user.mention} | {staff_role.mention}", embed=embed, view=view)
            
            # Auto-response
            auto_msg = await channel.send("⏳ A staff member will be with you shortly!")
            
            await interaction.response.send_message(
                embed=EmbedBuilder.success(f"Ticket created: {channel.mention}"),
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                embed=EmbedBuilder.error(f"Error: {str(e)}"),
                ephemeral=True
            )

class TicketControlView(discord.ui.View):
    def __init__(self, ticket_id: str):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
    
    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green, emoji="✅", custom_id="claim_ticket")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role_id = 1441463909155344576
        staff_role = interaction.guild.get_role(staff_role_id)
        
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message(
                embed=EmbedBuilder.error("Only staff can claim tickets!"),
                ephemeral=True
            )
            return
        
        ticket = db.get_ticket(self.ticket_id)
        if ticket and ticket.get("claimed_by"):
            claimer = interaction.guild.get_member(int(ticket["claimed_by"]))
            await interaction.response.send_message(
                embed=EmbedBuilder.error(f"Already claimed by {claimer.mention}"),
                ephemeral=True
            )
            return
        
        if db.claim_ticket(self.ticket_id, str(interaction.user.id)):
            # Update channel permissions
            await interaction.channel.set_permissions(
                interaction.user,
                read_messages=True,
                send_messages=True,
                manage_messages=True
            )
            
            # Update embed
            embed = interaction.message.embeds[0]
            embed.add_field(name="✅ Claimed By", value=interaction.user.mention, inline=False)
            embed.color = WARNING_COLOR
            
            await interaction.message.edit(embed=embed)
            await interaction.response.send_message(
                f"✅ {interaction.user.mention} has claimed this ticket!"
            )
    
    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket = db.get_ticket(self.ticket_id)
        if not ticket:
            return
        
        staff_role_id = 1441463909155344576
        staff_role = interaction.guild.get_role(staff_role_id)
        is_staff = staff_role in interaction.user.roles
        is_owner = str(interaction.user.id) == ticket["user_id"]
        
        if not (is_staff or is_owner):
            await interaction.response.send_message(
                embed=EmbedBuilder.error("You cannot close this ticket!"),
                ephemeral=True
            )
            return
        
        view = ConfirmCloseView(self.ticket_id)
        await interaction.response.send_message(
            "⚠️ Are you sure you want to close this ticket?",
            view=view,
            ephemeral=True
        )

class ConfirmCloseView(discord.ui.View):
    def __init__(self, ticket_id: str):
        super().__init__(timeout=60)
        self.ticket_id = ticket_id
    
    @discord.ui.button(label="Yes, Close & Rate", style=discord.ButtonStyle.red, emoji="🔒")
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Close ticket
        ticket = db.close_ticket(self.ticket_id, str(interaction.user.id))
        if not ticket:
            await interaction.followup.send(
                embed=EmbedBuilder.error("Ticket not found!"),
                ephemeral=True
            )
            return
        
        # Generate transcript
        transcript = generate_transcript(ticket)
        filename = f"transcripts/{self.ticket_id}.txt"
        os.makedirs("transcripts", exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        # Send to transcripts channel
        transcripts_channel_id = 1466878461632315527
        transcripts_channel = interaction.guild.get_channel(transcripts_channel_id)
        
        if transcripts_channel:
            file = discord.File(filename, f"{self.ticket_id}_transcript.txt")
            embed = discord.Embed(
                title=f"📝 Transcript • {self.ticket_id}",
                color=SUCCESS_COLOR,
                timestamp=datetime.now()
            )
            embed.add_field(name="Type", value=TICKET_TYPES[ticket['type']]['label'], inline=True)
            embed.add_field(name="User", value=f"<@{ticket['user_id']}>", inline=True)
            embed.add_field(name="Closed By", value=interaction.user.mention, inline=True)
            if ticket.get('claimed_by'):
                embed.add_field(name="Claimed By", value=f"<@{ticket['claimed_by']}>", inline=True)
            
            await transcripts_channel.send(embed=embed, file=file)
        
        # Ask for rating
        owner = interaction.guild.get_member(int(ticket['user_id']))
        if owner:
            try:
                rating_view = RatingView(self.ticket_id)
                await owner.send(
                    f"🔒 Your ticket `{self.ticket_id}` has been closed.\n"
                    f"Please rate your experience:",
                    view=rating_view
                )
            except:
                pass
        
        # Delete channel
        await interaction.followup.send("🔒 Closing ticket...", ephemeral=True)
        await interaction.channel.send("This ticket will close in 5 seconds...")
        
        import asyncio
        await asyncio.sleep(5)
        await interaction.channel.delete()
        
        # Cleanup
        os.remove(filename)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="❌ Cancelled.",
            view=None
        )

class RatingView(discord.ui.View):
    def __init__(self, ticket_id: str):
        super().__init__(timeout=300)
        self.ticket_id = ticket_id
    
    @discord.ui.button(label="⭐", style=discord.ButtonStyle.primary)
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 1)
    
    @discord.ui.button(label="⭐⭐", style=discord.ButtonStyle.primary)
    async def rate_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 2)
    
    @discord.ui.button(label="⭐⭐⭐", style=discord.ButtonStyle.primary)
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 3)
    
    @discord.ui.button(label="⭐⭐⭐⭐", style=discord.ButtonStyle.primary)
    async def rate_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 4)
    
    @discord.ui.button(label="⭐⭐⭐⭐⭐", style=discord.ButtonStyle.green)
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, 5)
    
    async def submit_rating(self, interaction: discord.Interaction, rating: int):
        db.add_rating(self.ticket_id, rating)
        await interaction.response.send_message(
            f"⭐ Thank you for rating us {rating}/5!",
            ephemeral=True
        )
        self.stop()

def generate_transcript(ticket: dict) -> str:
    lines = [
        "=" * 60,
        "WEST SERVICES • TICKET TRANSCRIPT",
        "=" * 60,
        f"Ticket ID: {ticket['id']}",
        f"Type: {TICKET_TYPES.get(ticket['type'], {}).get('label', ticket['type'])}",
        f"Created: {ticket['created_at']}",
        f"Closed: {ticket.get('closed_at', 'N/A')}",
        "=" * 60,
        "",
        "MESSAGES:",
        "-" * 60
    ]
    
    for msg in ticket.get("transcript", []):
        lines.append(f"[{msg['timestamp'][:19]}] {msg['author']}:")
        lines.append(f"  {msg['content']}")
        if msg.get('attachments'):
            lines.append(f"  [Attachments: {', '.join(msg['attachments'])}]")
        lines.append("")
    
    return "\n".join(lines)

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="ticketpanel", description="Send the ticket panel")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        banner_url = "https://cdn.discordapp.com/attachments/1466878461632315527/1475484445564862586/ticketpanl2_1_1.png"
        embed = EmbedBuilder.ticket_panel(banner_url)
        view = discord.ui.View(timeout=None)
        view.add_item(TicketTypeSelect())
        
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="add", description="Add a user to the ticket")
    @app_commands.describe(user="User to add")
    async def add_user(self, interaction: discord.Interaction, user: discord.Member):
        if not interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message(
                embed=EmbedBuilder.error("This is not a ticket channel!"),
                ephemeral=True
            )
            return
        
        await interaction.channel.set_permissions(user, read_messages=True, send_messages=True)
        await interaction.response.send_message(
            embed=EmbedBuilder.success(f"Added {user.mention} to the ticket!")
        )
    
    @app_commands.command(name="remove", description="Remove a user from the ticket")
    @app_commands.describe(user="User to remove")
    async def remove_user(self, interaction: discord.Interaction, user: discord.Member):
        if not interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message(
                embed=EmbedBuilder.error("This is not a ticket channel!"),
                ephemeral=True
            )
            return
        
        await interaction.channel.set_permissions(user, overwrite=None)
        await interaction.response.send_message(
            embed=EmbedBuilder.success(f"Removed {user.mention} from the ticket!")
        )
    
    @app_commands.command(name="rename", description="Rename the ticket")
    @app_commands.describe(name="New name")
    async def rename_ticket(self, interaction: discord.Interaction, name: str):
        if not interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message(
                embed=EmbedBuilder.error("This is not a ticket channel!"),
                ephemeral=True
            )
            return
        
        await interaction.channel.edit(name=f"ticket-{name}")
        await interaction.response.send_message(
            embed=EmbedBuilder.success(f"Renamed to `ticket-{name}`")
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))

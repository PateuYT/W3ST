import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import EmbedBuilder
from utils.database import TicketDatabase

db = TicketDatabase()

class Blacklist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="blacklist", description="Blacklist a user from tickets")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(user="User to blacklist", reason="Reason for blacklist")
    async def blacklist_add(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if db.is_blacklisted(str(user.id)):
            await interaction.response.send_message(
                embed=EmbedBuilder.error(f"{user.mention} is already blacklisted!"),
                ephemeral=True
            )
            return
        
        db.blacklist_add(str(user.id), reason, str(interaction.user.id))
        await interaction.response.send_message(
            embed=EmbedBuilder.success(f"Blacklisted {user.mention}\nReason: {reason}")
        )
    
    @app_commands.command(name="unblacklist", description="Remove user from blacklist")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(user="User to unblacklist")
    async def blacklist_remove(self, interaction: discord.Interaction, user: discord.Member):
        if db.blacklist_remove(str(user.id)):
            await interaction.response.send_message(
                embed=EmbedBuilder.success(f"Removed {user.mention} from blacklist!")
            )
        else:
            await interaction.response.send_message(
                embed=EmbedBuilder.error(f"{user.mention} is not blacklisted!"),
                ephemeral=True
            )
    
    @app_commands.command(name="blacklistview", description="View blacklisted users")
    @app_commands.checks.has_permissions(administrator=True)
    async def blacklist_view(self, interaction: discord.Interaction):
        if not db.data['blacklist']:
            await interaction.response.send_message(
                embed=EmbedBuilder.info("No users are blacklisted."),
                ephemeral=True
            )
            return
        
        embed = discord.Embed(title="🚫 Blacklisted Users", color=0xDC2626)
        
        for entry in db.data['blacklist']:
            user = self.bot.get_user(int(entry['user_id']))
            name = user.mention if user else f"User ID: {entry['user_id']}"
            
            embed.add_field(
                name=name,
                value=f"Reason: {entry['reason']}\nBy: <@{entry['added_by']}>",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Blacklist(bot))

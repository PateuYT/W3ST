import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import EmbedBuilder
from utils.database import TicketDatabase

db = TicketDatabase()

class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="stats", description="View ticket statistics")
    async def view_stats(self, interaction: discord.Interaction):
        stats = db.get_stats()
        avg_rating = db.get_average_rating()
        
        embed = EmbedBuilder.stats(stats, avg_rating)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="mytickets", description="View your ticket history")
    async def my_tickets(self, interaction: discord.Interaction):
        user_tickets = {k: v for k, v in db.data['tickets'].items() 
                       if v['user_id'] == str(interaction.user.id)}
        
        if not user_tickets:
            await interaction.response.send_message(
                embed=EmbedBuilder.info("You have no ticket history."),
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🎫 Your Ticket History",
            color=0xDC2626
        )
        
        for tid, ticket in list(user_tickets.items())[:10]:  # Last 10
            status = "🟢 Open" if ticket['status'] == 'open' else "🔒 Closed"
            rating = f"⭐ {ticket['rating']['stars']}/5" if ticket.get('rating') else "Not rated"
            
            embed.add_field(
                name=f"{tid} • {ticket['type'].capitalize()}",
                value=f"Status: {status} | Rating: {rating}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Stats(bot))

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
GUILD_ID = 1437853582161477695

class WestBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            help_command=None
        )
    
    async def setup_hook(self):
        # Load cogs
        await self.load_extension("cogs.tickets")
        await self.load_extension("cogs.stats")
        await self.load_extension("cogs.blacklist")
        await self.load_extension("cogs.autoresponder")
        
        # Sync commands
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        
        print(f"Loaded {len(self.cogs)} cogs")
        print(f"Synced commands to guild {GUILD_ID}")
    
    async def on_ready(self):
        print(f"🚀 West Ticket Bot is online!")
        print(f"Logged in as: {self.user.name} ({self.user.id})")
        print(f"Guild: {GUILD_ID}")
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="🎫 Tickets | West Services"
            )
        )

bot = WestBot()

# Error handling
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to use this command!",
                color=0xEF4444
            ),
            ephemeral=True
        )
    else:
        raise error

# Run bot
if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("Error: BOT_TOKEN not found in .env file!")
        exit(1)
    
    bot.run(token)

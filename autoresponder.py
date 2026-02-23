import discord
from discord.ext import commands

class AutoResponder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.responses = {
            'order': [
                "Thanks for your order! Please provide:\n• What service you need\n• Your budget\n• Any specific requirements",
                "A staff member will assist you shortly with your order!"
            ],
            'support': [
                "Thanks for contacting support! Please describe your issue in detail.",
                "While you wait, you can check our FAQ: discord.gg/west-faq"
            ],
            'refund': [
                "Refund request received. Please provide:\n• Order ID/Transaction ID\n• Reason for refund\n• Date of purchase",
                "Refunds are processed within 24-48 hours."
            ],
            'staff': [
                "Thanks for your interest in joining West Services!",
                "Please tell us:\n• Your age\n• Your timezone\n• Previous experience\n• Why you want to join"
            ]
        }
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        # Check if in ticket channel
        if not message.channel.name.startswith("ticket-"):
            return
        
        # Find ticket
        from utils.database import TicketDatabase
        db = TicketDatabase()
        
        ticket = None
        for tid, tdata in db.data['tickets'].items():
            if str(tdata['channel_id']) == str(message.channel.id) and tdata['status'] == 'open':
                ticket = tdata
                break
        
        if not ticket:
            return
        
        # Check if first message from user
        user_messages = [m for m in ticket.get('transcript', []) 
                        if m['author'] == f"{message.author.name}#{message.author.discriminator}"]
        
        if len(user_messages) == 0:  # First message
            responses = self.responses.get(ticket['type'], [])
            for resp in responses:
                await message.channel.send(resp)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoResponder(bot))

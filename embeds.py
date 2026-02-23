import discord
from datetime import datetime

# Colors
PRIMARY_COLOR = 0xDC2626      # Red
SUCCESS_COLOR = 0x22C55E      # Green
WARNING_COLOR = 0xF59E0B      # Yellow
ERROR_COLOR = 0xEF4444        # Red error
INFO_COLOR = 0x3B82F6         # Blue

class EmbedBuilder:
    @staticmethod
    def ticket_panel(banner_url: str = None) -> discord.Embed:
        embed = discord.Embed(
            title="🎫 West Services • Support System",
            description=(
                "**Welcome to West Services!**\n\n"
                "Our professional team is ready to assist you.\n"
                "Select a category below to create your ticket.\n\n"
                "⏱️ **Response Time:** 5-20 minutes\n"
                "🕐 **Available:** 24/7\n"
                "⭐ **Average Rating:** 4.8/5"
            ),
            color=PRIMARY_COLOR,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📋 Categories",
            value=(
                "🛠️ **Support** — General help & assistance\n"
                "🛒 **Order** — Purchase our services\n"
                "👔 **Staff Application** — Join our team\n"
                "💰 **Refund** — Request a refund"
            ),
            inline=False
        )
        
        embed.set_image(url=banner_url) if banner_url else None
        embed.set_footer(text="West Services • Premium Quality", icon_url=None)
        
        return embed
    
    @staticmethod
    def ticket_welcome(ticket_type: str, ticket_info: dict, user: discord.Member) -> discord.Embed:
        emojis = {
            'support': '🛠️',
            'order': '🛒',
            'staff': '👔',
            'refund': '💰'
        }
        
        messages = {
            'support': "Welcome! How can we help you today?",
            'order': "Welcome! Please describe what you'd like to purchase.",
            'staff': "Welcome! Please tell us about yourself and why you want to join.",
            'refund': "Welcome! Please provide your order details and reason for refund."
        }
        
        embed = discord.Embed(
            title=f"{emojis.get(ticket_type, '🎫')} {ticket_info['label']} Ticket",
            description=messages.get(ticket_type, "How can we help?"),
            color=PRIMARY_COLOR,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="🎫 Ticket ID", value=f"`{ticket_info['id']}`", inline=True)
        embed.add_field(name="👤 User", value=user.mention, inline=True)
        embed.add_field(name="⏰ Created", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
        embed.add_field(name="📊 Status", value="⏳ Waiting for support", inline=True)
        
        return embed
    
    @staticmethod
    def error(message: str, title: str = "❌ Error") -> discord.Embed:
        return discord.Embed(title=title, description=message, color=ERROR_COLOR)
    
    @staticmethod
    def success(message: str, title: str = "✅ Success") -> discord.Embed:
        return discord.Embed(title=title, description=message, color=SUCCESS_COLOR)
    
    @staticmethod
    def info(message: str, title: str = "ℹ️ Info") -> discord.Embed:
        return discord.Embed(title=title, description=message, color=INFO_COLOR)
    
    @staticmethod
    def stats(stats_data: dict, avg_rating: float) -> discord.Embed:
        embed = discord.Embed(
            title="📊 West Services • Statistics",
            color=PRIMARY_COLOR,
            timestamp=datetime.now()
        )
        
        # Tickets created
        created = stats_data.get('tickets_created', {})
        total_created = sum(created.values())
        embed.add_field(
            name="🎫 Tickets Created",
            value=f"**Total:** {total_created}\n" + "\n".join([
                f"{k.capitalize()}: {v}" for k, v in created.items()
            ]) if created else "No data",
            inline=True
        )
        
        # Tickets closed
        closed = stats_data.get('tickets_closed', {})
        total_closed = sum(closed.values())
        embed.add_field(
            name="🔒 Tickets Closed",
            value=f"**Total:** {total_closed}\n" + "\n".join([
                f"{k.capitalize()}: {v}" for k, v in closed.items()
            ]) if closed else "No data",
            inline=True
        )
        
        # Ratings
        ratings = stats_data.get('ratings', {})
        embed.add_field(
            name="⭐ Ratings",
            value=f"**Average:** {avg_rating:.1f}/5\n" + "\n".join([
                f"{'⭐' * int(k)}: {v}" for k, v in sorted(ratings.items(), key=lambda x: int(x[0]))
            ]) if ratings else "No ratings yet",
            inline=True
        )
        
        return embed

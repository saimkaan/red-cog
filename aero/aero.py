import discord
from redbot.core import commands

class Aero(commands.Cog):
    """My custom cog"""

    def __init__(self, bot):
        self.bot = bot
            
    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        if message.author.bot:
            return
        if "aero" in message.content.lower():
            async with message.channel.typing():
                await message.reply("Aero says fuck you, and TA is fake news")
            return
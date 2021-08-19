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
        if "foo" or "Foo" in message.content:
            async with message.channel.typing():
                await message.reply("bar")
            return

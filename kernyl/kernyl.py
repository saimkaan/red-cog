import discord
from redbot.core import commands

class Kernyl(commands.Cog):
    """My custom cog to troll Kernyl"""

    def __init__(self, bot):
        self.bot = bot
            
    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        if message.author.bot:
            return
        if "kernyl" in message.content.lower():
            async with message.channel.typing():
                await message.reply("Did you know that Kernyl is up 6% today!")
                await message.reply("<:aerofarmer:877661371523793008>")
            return
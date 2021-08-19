import discord
from redbot.core import commands

class Aero(commands.Cog):
    """My custom cog"""

    def __init__(self, bot):
        self.bot = bot
            
    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        print(f"{message.author.name}: {message.content}")
        logger.debug(f"{message.author.name}: {message.content}")

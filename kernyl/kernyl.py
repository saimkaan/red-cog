import discord
from redbot.core import commands

class Kernyl(commands.Cog):
    """My custom cog"""

    def __init__(self, bot):
        self.bot = bot
   
    @commands.Cog.listener()
    async def on_message(message):
        if message.channel.id == 811566276039540746:
            target_channel = self.bot.get_channel(956314205902999572)
                await target_channel.send(message.embeds[0])

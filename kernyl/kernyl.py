import discord
from redbot.core import commands

class Kernyl(commands.Cog):
    """My custom cog"""

    def __init__(self, bot):
        self.bot = bot
   
    @commands.Cog.listener()
    async def on_message(message):
        if message.channel.id == 804524249464700942:
            target_channel = self.bot.get_channel(951076247042146314)
            await target_channel.send(embed=message.embeds[0].copy())
            await target_channel.send(message.content)

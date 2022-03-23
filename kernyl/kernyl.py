import discord
from redbot.core import commands

class Kernyl(commands.Cog):
    """My custom cog to troll Kernyl"""

    def __init__(self, bot):
        self.bot = bot
   
    @commands.Cog.listener()
        async def on_message(message):
        if message.channel.id == 951076247042146314:
            target_channel = bot.get_channel(833785942636232755)
            await target_channel.send(message.content)
  

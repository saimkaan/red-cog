import discord
from redbot.core import commands

class Kernyl(commands.Cog):
    """My custom cog"""

    def __init__(self, bot):
        self.bot = bot
   
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
    if message.channel.id == 804524249464700942:
        target_channel = bot.get_channel(999601740561252372)
        await target_channel.send(message.content)

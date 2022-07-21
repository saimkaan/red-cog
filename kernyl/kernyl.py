import discord
from redbot.core import commands

class Kernyl(commands.Cog):
    """My custom cog"""

    def __init__(self, bot):
        self.bot = bot
   
    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        if message.author.bot:
            return
        if message.author.user:
            return
        if message.channel.id == 804524249464700942:
            target_channel = self.bot.get_channel(999601740561252372)
            await target_channel.send(message.content)
            await target_channel.send(embed=message.embeds[0])

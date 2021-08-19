from redbot.core import commands

class Aero(commands.Cog):
    """My custom cog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        if client.user.id != message.author.id:
            if 'foo' in message.content:
                await client.send_message(message.channel, 'bar')

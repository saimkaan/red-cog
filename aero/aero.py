from redbot.core import commands

class Aero(commands.Cog):
    """My custom cog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def on_message_without_command(message):
        if 'foo' in message.content:
            await client.send_message(message.channel, 'bar')

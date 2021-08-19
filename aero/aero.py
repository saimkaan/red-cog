from redbot.core import commands

class Aero(commands.Cog):
    """My custom cog for Aero"""

    def __init__(self, bot):
        self.bot = bot

    @commands.event
    async def on_message(message):
        if client.user.id != message.author.id:
            if 'aero' in message.content:
                await client.send_message(message.channel, 'Aero says fuck you, and TA is fake news')
        await client.process_commands(message)
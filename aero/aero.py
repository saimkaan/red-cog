from discord.ext import commands

class Aero(commands.Cog):
    """My custom cog for Aero"""

    def __init__(self, bot):
        self.bot = bot
        
    client = commands.Bot(command_prefix='!')
    
    @client.event
    async def on_ready():
        print('client ready')

    @client.command()
    async def ping():
        await client.say('Pong')

    @client.event
    async def on_message(message):
        if client.user.id != message.author.id:
            if 'foo' in message.content:
                await client.send_message(message.channel, 'bar')
        await client.process_commands(message)

import discord
from discord.ext import commands

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

client.run('TOKEN')

import discord
from redbot.core import commands

class Kernyl(commands.Cog):
    """My custom cog to troll Kernyl"""

    def __init__(self, bot):
        self.bot = bot
     
        
   
    @commands.Cog.listener()
    async def on_message(message):
        if message.author.bot:
            return
        if message.channel.id == '944022733262569562':
            const msgLog = '[MESSAGE] [${message.guild.name}] [#${message.channel.name}] ${message.author.username}#${message.author.discriminator}: ${message.content}\n'
            bot.channels.get('956215619777359892').send(msgLog)
            return
  

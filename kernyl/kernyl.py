import discord
from redbot.core import commands

class Kernyl(commands.Cog):
    """My custom cog to troll Kernyl"""

    def __init__(self, bot):
        self.bot = bot
        
    
            
    @commands.Cog.listener()
async def on_message(message):
    if message.channel.id == '944022733262569562':
        author_name = message.author.name + "#" + message.author.discriminator
        if len(message.attachments) > 0:
            image_url = message.attachments[0].url
        else:
            image_url = ""
        await send_message(build_embed(author_name, message.author.avatar_url_as(format=None, static_format='png', size=1024), message.clean_content, message.author.color, image_url))

async def send_message(message_embed):
    channel = target_client.get_channel('956215619777359892')
    await channel.send(embed=message_embed)

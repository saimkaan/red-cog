import discord
import discord
import asyncio
import re
import os
from redbot.core import commands

class Kernyl(commands.Cog):
    """My custom cog to troll Kernyl"""

    def __init__(self, bot):
        self.bot = bot
     
    def find_url(string):
    url = re.findall("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", string)
    return url


    def build_embed(author_name, author_picture, embed_desc, embed_color, embed_image):
        emb = discord.Embed()
        emb.set_author(name=author_name, url="", icon_url=author_picture)
        emb.description = embed_desc
        emb.color = embed_color
        message_urls = find_url(embed_desc)
        if embed_image != "":
            emb.set_image(url=embed_image)
            print(author_name + " uploaded an image")
        elif len(message_urls) > 0:
            emb.set_image(url=message_urls[0])
            print(author_name + " linked an image")
        else:
            print(author_name + ": " + embed_desc)
        return emb
   
    @commands.Cog.listener()
    async def on_message(message):
        if message.channel.id == '944022733262569562':
            author_name = message.author.name + "#" + message.author.discriminator
            if len(message.attachments) > 0:
                image_url = message.attachments[0].url
            else:
                image_url = ""
            await send_message(build_embed(author_name, message.author.avatar_url_as(format=None, static_format='png', size=1024), message.clean_content, message.author.color, image_url))
    
    @commands.Cog.listener()
    async def send_message(message_embed):
        channel = bot.get_channel('956215619777359892')
        await channel.send(embed=message_embed)
  

from redbot.core import commands, Config
import re

import re
from discord.ext import commands

class VxTwitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if "twitter.com" in message.content:
            new_message = re.sub(r"(https?://)?(www\.)?twitter\.com/(\w+)/status/(\d+)", r"https://vxtwitter.com/\3/status/\4", message.content)
            if "vxtwitter.com" in new_message or "fixvx.com" in new_message:
                await message.channel.send(f"{new_message} from: {message.author.mention}")
            else:
                await message.channel.send(f"{new_message} from: {message.author.mention}")
                await message.delete()
        if "x.com" in message.content:
            new_message = re.sub(r"(https?://)?(www\.)?x\.com/(\w+)/status/(\d+)", r"https://fixvx.com/\3/status/\4", message.content)
            if "vxtwitter.com" in new_message or "fixvx.com" in new_message:
                await message.channel.send(f"{new_message} from: {message.author.mention}")
            else:
                await message.channel.send(f"{new_message} from: {message.author.mention}")
                await message.delete()

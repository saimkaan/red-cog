from redbot.core import commands
import re
import time

class VxTwitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if "twitter.com" in message.content and "vxtwitter.com" not in message.content:
            new_message = re.sub(r"(https?://)?(www\.)?twitter\.com/(\w+)/status/(\d+)", r"https://vxtwitter.com/\3/status/\4", message.content)
            if len(message.embeds) == 0:
                await message.channel.send(f"{new_message} from: {message.author.mention}")
                await message.delete()
        if "x.com" in message.content and "fixvx.com" not in message.content:
            new_message = re.sub(r"(https?://)?(www\.)?x\.com/(\w+)/status/(\d+)", r"https://fixvx.com/\3/status/\4", message.content)
            if len(message.embeds) == 0:
                await message.channel.send(f"{new_message} from: {message.author.mention}")
                await message.delete()
        if "tiktok.com" in message.content and "vxtiktok.com" not in message.content:
            new_message = re.sub(r"(https?://)?(www\.)?tiktok\.com/(\w+)/status/(\d+)", r"https://vxtiktok.com/\3/status/\4", message.content)
            if len(message.embeds) == 0:
                await message.channel.send(f"{new_message} from: {message.author.mention}")
                await message.delete()

from redbot.core import commands, Config
import re

class VxTwitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if "twitter.com" in message.content:
            new_message = re.sub(r"(https?://)?(www\.)?twitter\.com/(\w+)/status/(\d+)", r"https://vxtwitter.com/\3/status/\4", message.content)
            await message.channel.send(new_message)
            await message.delete()
        if "x.com" in message.content:
            new_message = re.sub(r"(https?://)?(www\.)?x\.com/(\w+)/status/(\d+)", r"https://fixvx.com/\3/status/\4", message.content)
            await message.channel.send(new_message)
            await message.delete()
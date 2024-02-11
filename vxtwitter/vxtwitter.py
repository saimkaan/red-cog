from redbot.core import commands
import re

class VxTwitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
            
        # New command to convert Twitter video links
        if message.content.startswith("!video"):
            # Extract the Twitter video link
            match = re.match(r"!video (https?://twitter\.com/[^/]+/status/\d+)", message.content)
            if match:
                twitter_link = match.group(1)
                converted_link = re.sub(r"https?://twitter\.com/([^/]+)/status/(\d+)", r"https://d.fxtwitter.com/\1/status/\2", twitter_link)
                await message.channel.send(f"Converted link: {converted_link} from: {message.author.mention}")
                await message.delete()
        elif "twitter.com" in message.content and "vxtwitter.com" not in message.content:
            new_message = re.sub(r"(https?://)?(www\.)?twitter\.com/(.*)", r"https://vxtwitter.com/\3", message.content)
            await message.channel.send(f"{new_message} from: {message.author.mention}")
            await message.delete()
                
        # Twitter link replacement (unchanged)
        #if "twitter.com" in message.content and "vxtwitter.com" not in message.content:
            #new_message = re.sub(r"(https?://)?(www\.)?twitter\.com/(.*)", r"https://vxtwitter.com/\3", message.content)
            #await message.channel.send(f"{new_message} from: {message.author.mention}")
            #await message.delete()
            
        # TikTok link replacement (unchanged)
        if "tiktok.com" in message.content and "vxtiktok.com" not in message.content:
            new_message = re.sub(r"(https?://)?(www\.)?tiktok\.com/(.*)", r"https://vxtiktok.com/\3", message.content)
            await message.channel.send(f"{new_message} from: {message.author.mention}")
            await message.delete()

        # Existing code for x.com links (unchanged)
        if "x.com" in message.content and "fixvx.com" not in message.content:
            new_message = re.sub(r"(https?://)?(www\.)?x\.com/(.*)", r"https://fixvx.com/\3", message.content)
            await message.channel.send(f"{new_message} from: {message.author.mention}")
            await message.delete()
            
        # Instagram link replacement (unchanged)
        if "instagram.com" in message.content and "ddinstagram.com" not in message.content:
            new_message = re.sub(r"(https?://)?(www\.)?instagram\.com/(.*)", r"https://www.ddinstagram.com/\3", message.content)
            await message.channel.send(f"{new_message} from: {message.author.mention}")
            await message.delete()

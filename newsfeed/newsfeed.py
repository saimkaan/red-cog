from redbot.core import commands, Config
import aiohttp
import asyncio
import discord
import datetime
import pytz

class NewsFeed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1231231337)
        default_guild = {"channels": []}
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()
        self.url = "https://phx.unusualwhales.com/api/news/headlines-feed?limit=10"
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        self.data = []
        self.task = asyncio.create_task(self.fetch_data())

    def cog_unload(self):
        if self.task:
            self.task.cancel()
            self.task = None
        asyncio.create_task(self.session.close())


    @commands.group()
    async def newsfeed(self, ctx):
        pass

    @newsfeed.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id in channels:
                await ctx.send(f"{channel.mention} is already a news feed channel.")
                return
            channels.append(channel.id)
            await ctx.send(f"{channel.mention} set as a news feed channel.")

    @newsfeed.command()
    async def removechannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id not in channels:
                await ctx.send(f"{channel.mention} is not a news feed channel.")
                return
            channels.remove(channel.id)
            await ctx.send(f"{channel.mention} removed as a news feed channel.")

    @newsfeed.command()
    async def listchannels(self, ctx):
        channels = await self.config.guild(ctx.guild).channels()
        if not channels:
            await ctx.send("No news feed channels set.")
            return
        channel_mentions = [f"<#{channel_id}>" for channel_id in channels]
        await ctx.send(f"News feed channels: {', '.join(channel_mentions)}")

    async def fetch_data(self):
        while True:
            try:
                async with self.session.get(self.url, headers=self.headers) as resp:
                    json_data = await resp.json()
                    new_data = [item for item in json_data["data"] if item not in self.data and item["is_major"]]
                    if new_data:
                        for guild in self.bot.guilds:
                            channels = await self.config.guild(guild).channels()
                            for channel_id in channels:
                                channel = guild.get_channel(channel_id)
                                for item in new_data:
                                    if item["tickers"]:
                                        tickers = ", ".join(item["tickers"])
                                        embed = discord.Embed(title=f"**{tickers}**", description=f"**{item['headline']}**", timestamp=datetime.datetime.now(pytz.utc))
                                    else:
                                        embed = discord.Embed(description=f"**{item['headline']}**", timestamp=datetime.datetime.now(pytz.utc))
                                    embed.set_footer(text=item["source"])
                                    await channel.send(embed=embed)
                        self.data.extend(new_data)
                await asyncio.sleep(5)
            except Exception as e:
                print(e)
                await asyncio.sleep(60)


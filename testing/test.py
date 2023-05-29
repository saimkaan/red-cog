from redbot.core import commands, Config
import aiohttp
import asyncio
import discord

class NewsFeed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {"channels": []}
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()
        self.url = "https://phx.unusualwhales.com/api/news/headlines-feed?limit=50"
        self.headers = {}
        self.data = []
        self.task = asyncio.create_task(self.fetch_data())

    def cog_unload(self):
        if self.task:
            self.task.cancel()
            self.task = None

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

    async def fetch_data(self):
        while True:
            try:
                async with self.session.get(self.url, headers=self.headers) as resp:
                    json_data = await resp.json()
                    new_data = [item for item in json_data["data"] if item not in self.data]
                    if new_data:
                        for guild in self.bot.guilds:
                            channels = await self.config.guild(guild).channels()
                            for channel_id in channels:
                                channel = guild.get_channel(channel_id)
                                for item in new_data:
                                    embed = discord.Embed(title=item["headline"], timestamp=item["created_at"])
                                    embed.set_footer(text=item["source"])
                                    await channel.send(embed=embed)
                        self.data.extend(new_data)
                await asyncio.sleep(5)
            except Exception as e:
                await asyncio.sleep(60)

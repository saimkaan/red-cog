import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
import requests
import asyncio

class Test(commands.Cog):
    """A cog that posts news headlines from a URL."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=133713371337)  # Use a unique identifier for your cog
        default_guild_settings = {"channel_ids": {}}
        self.config.register_guild(**default_guild_settings)
        self.url = "https://phx.unusualwhales.com/api/news/headlines-feed?limit=50"
        self.tasks = {}
        self.start()

    @commands.group()
    async def newsfeed(self, ctx):
        """Manage the news feed settings."""
        pass

    @newsfeed.command()
    async def setchannel(self, ctx, guild_id: int, channel: discord.TextChannel):
        """Set the channel where the news feed will be posted."""
        await self.config.guild(ctx.guild).channel_ids.set_raw(guild_id, value=channel.id)
        await ctx.send(f"News feed channel set to {channel.mention} for guild ID {guild_id}.")
        print(f"News feed channel set to {channel.mention} for guild ID {guild_id}")

    @newsfeed.command()
    async def removechannel(self, ctx, guild_id: int):
        """Remove the channel for the news feed on a specific guild."""
        await self.config.guild(ctx.guild).channel_ids.clear_raw(guild_id)
        await ctx.send(f"News feed channel removed for guild ID {guild_id}.")
        print(f"News feed channel removed for guild ID {guild_id}")

    @newsfeed.command()
    async def start(self, ctx, guild_id: int):
        """Start the news feed task on a specific guild."""
        channel_id = await self.config.guild(ctx.guild).channel_ids.get_raw(guild_id)
        if channel_id is None:
            await ctx.send("You need to set a channel first for the specified guild.")
            return

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            await ctx.send("Invalid channel. Please set a valid channel for the specified guild.")
            return

        if guild_id in self.tasks and not self.tasks[guild_id].done():
            await ctx.send("News feed is already running for the specified guild.")
        else:
            self.tasks[guild_id] = self.bot.loop.create_task(self.news_feed_loop(guild_id))
            await ctx.send("News feed started for the specified guild.")

    @newsfeed.command()
    async def stop(self, ctx, guild_id: int):
        """Stop the news feed task on a specific guild."""
        if guild_id in self.tasks and self.tasks[guild_id].done():
            await ctx.send("News feed is not running for the specified guild.")
        else:
            self.tasks[guild_id].cancel()
            await ctx.send("News feed stopped for the specified guild.")

    async def news_feed_loop(self, guild_id: int):
        """The loop that fetches and posts the news headlines for a specific guild."""
        # Initialize a set of seen headlines
        seen = set()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        while True:
            try:
                channel_id = await self.config.guild_from_id(guild_id).channel_ids()
                if channel_id is None:
                    continue  # Skip guilds without a configured channel
                channel = self.bot.get_channel(channel_id)
                if channel is None:
                    continue  # Skip invalid channels
                # Get the JSON data from the URL
                response = requests.get(self.url, headers=headers)
                response.raise_for_status()  # Raise an exception if the response is not 200 OK
                data = response.json()
                print(f"1")
                # Iterate over the data in reverse order (oldest to newest)
                for item in reversed(data["data"]):
                    print(f"2")
                    # Check if the headline is already seen
                    headline = item["headline"]
                    #is_major = item["is_major"]
                    #if is_major and headline not in seen:
                    if headline not in seen:
                        print(f"3")
                        # Add the headline to the seen set
                        seen.add(headline)
                        # Create an embed with the headline and other information
                        embed = discord.Embed(title=headline, url=item["url"], timestamp=item["created_at"])
                        embed.set_footer(text=f"Source: {item['source']}")
                        embed.add_field(name="Tickers", value=", ".join(item["tickers"]))
                        # Send the embed to the channel
                        await channel.send(embed=embed)
            except Exception as e:
                print(f"Error in news feed loop for guild ID {guild_id}: {e}")
                await asyncio.sleep(60)
            await asyncio.sleep(5)
            print(f"4")

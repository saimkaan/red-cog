import discord
from redbot.core import commands, Config
import requests
import asyncio

class Test(commands.Cog):
    """A cog that posts news headlines from a URL."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Use a unique identifier for your cog
        default_guild_settings = {"channel_id": None}
        self.config.register_guild(**default_guild_settings)
        self.url = "https://phx.unusualwhales.com/api/news/headlines-feed?limit=50"
        self.task = None

    @commands.group()
    async def newsfeed(self, ctx):
        """Manage the news feed settings."""
        pass

    @newsfeed.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel where the news feed will be posted."""
        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        await ctx.send(f"News feed channel set to {channel.mention}.")

    @newsfeed.command()
    async def start(self, ctx):
        """Start the news feed task."""
        channel_id = await self.config.guild(ctx.guild).channel_id()
        if channel_id is None:
            await ctx.send("You need to set a channel first.")
            return

        self.channel = self.bot.get_channel(channel_id)
        if self.channel is None:
            await ctx.send("Invalid channel. Please set a valid channel.")
            return

        if self.task is None or not self.task.done():
            self.task = self.bot.loop.create_task(self.news_feed_loop())
            await ctx.send("News feed started.")
        else:
            await ctx.send("News feed is already running.")


    @newsfeed.command()
    async def stop(self, ctx):
        """Stop the news feed task."""
        if self.task is not None and self.task.is_running():
            self.task.cancel()
            await ctx.send("News feed stopped.")
        else:
            await ctx.send("News feed is not running.")

    async def news_feed_loop(self):
        """The loop that fetches and posts the news headlines."""
        # Initialize a set of seen headlines
        seen = set()
        while True:
            try:
                # Get the JSON data from the URL
                response = requests.get(self.url)
                response.raise_for_status()  # Raise an exception if the response is not 200 OK
                data = response.json()
                # Iterate over the data in reverse order (oldest to newest)
                for item in reversed(data["data"]):
                    # Check if the headline is already seen
                    headline = item["headline"]
                    is_major = item["is_major"]
                    if is_major and headline not in seen:
                        # Add the headline to the seen set
                        seen.add(headline)
                        # Create an embed with the headline and other information
                        embed = discord.Embed(title=headline, url=item["url"], timestamp=item["created_at"])
                        embed.set_footer(text=f"Source: {item['source']}")
                        embed.add_field(name="Tickers", value=", ".join(item["tickers"]))
                        # Send the embed to the channel
                        await self.channel.send(embed=embed)
            except Exception as e:
                # Log the error and continue the loop
                self.bot.logger.error(f"Error in news feed loop: {e}")
            finally:
                # Wait for 5 seconds before repeating
                await asyncio.sleep(5)

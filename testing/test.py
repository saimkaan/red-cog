import discord
import asyncio
import aiohttp
import datetime
from redbot.core import commands, Config


# Creating a cog class
class NewsFeed(commands.Cog):
    """A cog that posts news from a website."""

    # Initializing the cog
    def __init__(self, bot):
        self.bot = bot
        self.url = "https://phx.unusualwhales.com/api/news/headlines-feed?limit=50"  # The URL to get the news from
        self.data = None  # The data structure to store the news
        self.config = Config.get_conf(self, identifier=1234567890)  # Use a unique identifier for your cog
        self.config.register_guild(channels={})  # Register the guild-level channels data
        self.check_news_task = None

    async def initialize(self):
        """Load the stored channels data when the cog is initialized."""
        await self.config.guild_from_id(self.bot.guild.id).channels()

    # A command to add a channel to receive news
    @commands.command()
    async def addnewschannel(self, ctx, channel: discord.TextChannel):
        """Adds a channel to receive news from the website."""
        channels = await self.config.guild(ctx.guild).channels()
        # Check if the channel is already in the dictionary
        if channel.id in channels:
            await ctx.send("This channel is already receiving news.")
            return
        # Add the channel to the dictionary with the guild id as the key
        channels[channel.id] = True
        await self.config.guild(ctx.guild).channels.set(channels)
        await ctx.send(f"Added {channel.mention} to receive news.")

    # A command to remove a channel from receiving news
    @commands.command()
    async def removenewschannel(self, ctx, channel: discord.TextChannel):
        """Removes a channel from receiving news from the website."""
        channels = await self.config.guild(ctx.guild).channels()
        # Check if the channel is in the dictionary
        if channel.id not in channels:
            await ctx.send("This channel is not receiving news.")
            return
        # Remove the channel from the dictionary
        del channels[channel.id]
        await self.config.guild(ctx.guild).channels.set(channels)
        await ctx.send(f"Removed {channel.mention} from receiving news.")

    # A background task that runs every 5 seconds
    async def check_news(self):
        """Checks for new news from the website and posts them to the channels."""
        while True:
            await asyncio.sleep(5)  # Wait for 5 seconds
            channels = await self.config.guild(self.bot.guild).channels()
            # Get the data from the URL as JSON (you need to import aiohttp for this)
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    data = await response.json()
            # Check if there is any data
            if not data["data"]:
                continue
            # Check if there is any new data
            if data == self.data:
                continue
            # Store the new data
            self.data = data
            # Loop through each news item in reverse order (to post oldest first)
            for item in reversed(data["data"]):
                # Create an embed with the news information
                embed = discord.Embed(title=item["headline"], color=discord.Color.blue())
                embed.set_footer(text=f"Source: {item['source']}")
                embed.timestamp = datetime.datetime.fromisoformat(item["created_at"])
                # Loop through each channel in the dictionary
                for channel_id in channels:
                    # Get the channel object from the bot
                    channel = self.bot.get_channel(int(channel_id))
                    # Check if the channel exists
                    if channel:
                        # Send the embed to the channel
                        await channel.send(embed=embed)

    # A command to start the background task
    @commands.command()
    async def startnews(self, ctx):
        """Starts the background task to fetch and post news."""
        if self.check_news_task:
            return
        await self.initialize()
        self.check_news_task = asyncio.create_task(self.check_news())

    # A command to stop the background task
    @commands.command()
    async def stopnews(self, ctx):
        """Stops the background task."""
        if self.check_news_task:
            self.check_news_task.cancel()
            self.check_news_task = None
            await ctx.send("News feed stopped.")

    # A listener that starts the background task when the bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        """Starts the background task when the bot is ready."""
        await self.initialize()
        await self.startnews(self.bot.guild)

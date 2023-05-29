import discord
from redbot.core import commands, tasks

# Creating a cog class
class NewsFeed(commands.Cog):
    """A cog that posts news from a website."""

    # Initializing the cog
    def __init__(self, bot):
        self.bot = bot
        self.url = "https://phx.unusualwhales.com/api/news/headlines-feed?limit=50" # The URL to get the news from
        self.data = None # The data structure to store the news
        self.channels = {} # A dictionary to store the channels that should receive the news

    # A command to add a channel to receive news
    @commands.command()
    async def addnewschannel(self, ctx, channel: discord.TextChannel):
        """Adds a channel to receive news from the website."""
        # Check if the channel is already in the dictionary
        if channel.id in self.channels:
            await ctx.send("This channel is already receiving news.")
            return
        # Add the channel to the dictionary with the guild id as the key
        self.channels[channel.id] = ctx.guild.id
        await ctx.send(f"Added {channel.mention} to receive news.")

    # A command to remove a channel from receiving news
    @commands.command()
    async def removenewschannel(self, ctx, channel: discord.TextChannel):
        """Removes a channel from receiving news from the website."""
        # Check if the channel is in the dictionary
        if channel.id not in self.channels:
            await ctx.send("This channel is not receiving news.")
            return
        # Remove the channel from the dictionary
        del self.channels[channel.id]
        await ctx.send(f"Removed {channel.mention} from receiving news.")

    # A background task that runs every 5 seconds
    @tasks.loop(seconds=5)
    async def check_news(self):
        """Checks for new news from the website and posts them to the channels."""
        # Get the data from the URL as JSON
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                data = await response.json()
        # Check if there is any data
        if not data["data"]:
            return
        # Check if there is any new data
        if data == self.data:
            return
        # Store the new data
        self.data = data
        # Loop through each news item in reverse order (to post oldest first)
        for item in reversed(data["data"]):
            # Create an embed with the news information
            embed = discord.Embed(title=item["headline"], color=discord.Color.blue())
            embed.set_footer(text=f"Source: {item['source']}")
            embed.timestamp = datetime.datetime.fromisoformat(item["created_at"])
            # Loop through each channel in the dictionary
            for channel_id, guild_id in self.channels.items():
                # Get the channel object from the bot
                channel = self.bot.get_channel(channel_id)
                # Check if the channel exists and is in the same guild as stored
                if channel and channel.guild.id == guild_id:
                    # Send the embed to the channel
                    await channel.send(embed=embed)

    # A listener that starts the background task when the bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        """Starts the background task when the bot is ready."""
        self.check_news.start()
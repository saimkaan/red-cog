from redbot.core import Config, app_commands, commands
from redbot.core.bot import Red
from discord.ext import tasks, Context
from discord import Embed
import requests
import datetime
import pytz

API_URL = 'https://phx.unusualwhales.com/api/news/headlines-feed?limit=10'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

class NewsCog(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.latest_headlines = set()
        self.channel_ids = []  # Store the added channel IDs
        self.fetch_data.start()

    def cog_unload(self):
        self.fetch_data.cancel()

    @tasks.loop(seconds=5)
    async def fetch_data(self):
        data = self._get_data()
        if data:
            new_headlines = set(data) - self.latest_headlines
            if new_headlines:
                sorted_headlines = sorted(new_headlines, key=lambda x: x[1])
                for headline, created_at, source in sorted_headlines:
                    embed = Embed(
                        title=headline,
                        color=await self.bot.get_embed_colour(channel)
                    )
                    embed.set_footer(text=source)
                    embed.timestamp = datetime.datetime.now(pytz.utc)  # Use UTC time
                    for channel_id in self.channel_ids:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            await channel.send(embed=embed)
                self.latest_headlines.update(new_headlines)

    def _get_data(self):
        try:
            response = requests.get(API_URL, headers=headers)
            if response.status_code == 200:
                json_data = response.json()
                headlines = [
                    (
                        headline['headline'],
                        headline['created_at'],
                        headline.get('source', "N/A"),
                    )
                    for headline in json_data['data']
                ]
                return headlines
            else:
                print(f'Failed to fetch data. Status code: {response.status_code}')
        except requests.RequestException as e:
            print(f'Failed to fetch data: {e}')
        return []
    
    @commands.command()
    async def add_channel(self, ctx: Context, channel: discord.TextChannel):
        if channel.id in self.channel_ids:
            await ctx.send("This channel is already added.")
        else:
            self.channel_ids.append(channel.id)
            await ctx.send(f"Channel {channel.mention} has been added.")

    @add_channel.error
    async def add_channel_error(self, ctx: Context, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Invalid channel. Please mention a valid text channel.")

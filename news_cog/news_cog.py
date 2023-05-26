from redbot.core import Config, commands
from redbot.core.bot import Red
from discord import Embed
import requests
import datetime
import pytz
import asyncio

API_URL = 'https://phx.unusualwhales.com/api/news/headlines-feed?limit=50'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

class NewsCog(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.latest_headlines = set()
        self.fetch_data_task = None
        self.start_fetch_data()

    def cog_unload(self):
        self.stop_fetch_data()

    def start_fetch_data(self):
        if self.fetch_data_task is None:
            self.fetch_data_task = self.bot.loop.create_task(self.fetch_data())

    def stop_fetch_data(self):
        if self.fetch_data_task is not None:
            self.fetch_data_task.cancel()
            self.fetch_data_task = None

    async def fetch_data(self):
        while True:
            try:
                data = await self._get_data()
                if data:
                    new_headlines = data - self.latest_headlines
                    if new_headlines:
                        sorted_headlines = sorted(new_headlines, key=lambda x: x[1])
                        channel_ids = self.get_channel_ids()
                        for guild_id, channel_ids in channel_ids.items():
                            guild = self.bot.get_guild(guild_id)
                            if guild:
                                for channel_id in channel_ids:
                                    channel = guild.get_channel(channel_id)
                                    if channel:
                                        for headline, created_at, source in sorted_headlines:
                                            embed = Embed(
                                                description=f"**{headline}**",
                                                color=await self.bot.get_embed_colour(channel)
                                            )
                                            embed.set_footer(text=source)
                                            embed.timestamp = datetime.datetime.now(pytz.utc)  # Use UTC time
                                            await channel.send(embed=embed)
                        self.latest_headlines.update(new_headlines)
                await asyncio.sleep(10)  # Wait for 10 seconds before fetching data again
            except Exception as e:
                print(f"An error occurred in fetch_data task: {e}")
                await asyncio.sleep(60)  # Wait for 1 minute before retrying

    def get_channel_ids(self):
        # Return a dictionary mapping guild IDs to a list of channel IDs to post to
        # Example: {guild_id: [channel_id1, channel_id2], guild_id2: [channel_id3]}
        channel_ids = {
            833763746073280522: [833763746073280529],  # Replace with your guild and channel IDs
            804524249464700939: [859784262232309821]
        }
        return channel_ids

    async def _get_data(self):
        try:
            response = await asyncio.get_event_loop().run_in_executor(None, lambda: requests.get(API_URL, headers=headers))
            if response.status_code == 200:
                json_data = response.json()
                headlines = {
                    (
                        headline['headline'],
                        headline['created_at'],
                        headline.get('source', "N/A"),
                    )
                    for headline in json_data['data']
                    if headline.get('is_major', False)
                    #if headline.get('source', "N/A") == "tradex" and headline.get('is_major', False)
                }
                return headlines
            else:
                print(f'Failed to fetch data. Status code: {response.status_code}')
        except requests.RequestException as e:
            print(f'Failed to fetch data: {e}')
        return set()

import discord
from discord.ext import commands
from discord import Embed
import requests
import asyncio
import time
import datetime


class HeadlinesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 833763746073280529  # Discord channel ID where you want to post the data
        self.api_url = 'https://phx.unusualwhales.com/api/news/headlines-feed?limit=10'
        self.latest_headlines = set()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user.name} ({self.bot.user.id})')
        print('------')
        channel = self.bot.get_channel(self.channel_id)
        while True:
            data = self.fetch_data()
            if data:
                new_headlines = set(data) - self.latest_headlines
                if new_headlines:
                    sorted_headlines = sorted(new_headlines, key=lambda x: x[1])
                    for headline, created_at, source, ticker in sorted_headlines:
                        epoch_time = self.convert_to_epoch(created_at)
                        ticker_info = ticker if ticker else " "
                        embed = Embed(
                            title=headline,
                            description=f'{ticker_info}    :    {source}    :    <t:{epoch_time}>',
                            color=discord.Color.red()
                        )
                        await channel.send(embed=embed)
                    self.latest_headlines.update(new_headlines)
            await asyncio.sleep(5)  # Wait for 5 seconds before refreshing

    def fetch_data(self):
        try:
            response = requests.get(self.api_url, headers=self.headers)
            if response.status_code == 200:
                json_data = response.json()
                headlines = [
                    (
                        headline['headline'],
                        headline['created_at'],
                        headline.get('source', "N/A"),
                        headline.get('ticker', None)
                    )
                    for headline in json_data['data']
                ]
                return headlines
            else:
                print(f'Failed to fetch data. Status code: {response.status_code}')
        except requests.RequestException as e:
            print(f'Failed to fetch data: {e}')
        return []

    def convert_to_epoch(self, timestamp):
        try:
            datetime_obj = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
            epoch_time = int(datetime_obj.timestamp()) + 7200  # Adding 2 hours (2 * 60 * 60 seconds)
            return epoch_time
        except ValueError:
            print(f'Failed to convert timestamp to epoch: {timestamp}')
            return 0
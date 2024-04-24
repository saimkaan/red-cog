from redbot.core import commands, Config, tasks
import requests
import discord
import logging
import threading
import time
from datetime import datetime, timedelta

RESERVOIR_API_URL = "https://api.reservoir.tools/orders/asks/v5?tokenSetId=contract%3A0x8a3749936e723325c6b645a0901470cd9e790b94&limit=10"
PIXELMON_API_URL = 'https://api-cp.pixelmon.ai/nft/get-relics-count'

headers = {
    "accept": "*/*",
    "x-api-key": "1d336873-3714-504d-ade9-e0017bc7f390"
}

class PixelmonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.printed_trainers = {}
        self.config = Config.get_conf(self, identifier=123456789)
        default_guild = {"channels": []}
        self.config.register_guild(**default_guild)
        self.check_pixelmon_data.start()

    def cog_unload(self):
        self.check_pixelmon_data.cancel()

    @tasks.loop(seconds=30)
    async def check_pixelmon_data(self):
        token_ids = self.fetch_reservoir_data()
        if token_ids:
            self.fetch_pixelmon_data_with_threads(token_ids)

    # Function to fetch data from Reservoir API and process token IDs
    def fetch_reservoir_data(self):
        try:
            response = requests.get(RESERVOIR_API_URL, headers=headers)
            data = response.json()
            if 'orders' in data:
                token_ids = []
                for order in data['orders']:
                    token_id = order['criteria']['data']['token']['tokenId']
                    token_ids.append(token_id)
                return token_ids
        except Exception as e:
            logging.error(f"Error occurred while fetching data from Reservoir API: {e}")
        return None

    # Function to fetch data from Pixelmon API and create database
    def fetch_pixelmon_data(self, trainer_id):
        try:
            payload = {'nftType': 'trainer', 'tokenId': str(trainer_id)}
            response = requests.post(PIXELMON_API_URL, json=payload)
            data = response.json()
            if 'result' in data and 'response' in data['result']:
                relics_response = data['result']['response']['relicsResponse']
                for relic in relics_response:
                    if relic['relicsType'] == 'silver' and relic['count'] > 0:
                        return {
                            'trainer_id': trainer_id,
                            'relics_count': relic['count']
                        }
        except Exception as e:
            logging.error(f"Error occurred while fetching data from Pixelmon API: {e}")
        return None

    # Function to handle fetching Pixelmon data with threads
    def fetch_pixelmon_data_with_threads(self, token_ids):
        threads = []
        for token_id in token_ids:
            thread = threading.Thread(target=self.fetch_and_send_pixelmon_data, args=(token_id,))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

    # Helper function to fetch and send Pixelmon data
    async def fetch_and_send_pixelmon_data(self, token_id):
        pixelmon_data = self.fetch_pixelmon_data(token_id)
        if pixelmon_data:
            if token_id not in self.printed_trainers or (datetime.now() - self.printed_trainers[token_id]) > timedelta(hours=24):
                channel_ids = await self.config.guild(ctx.guild).channels()
                for channel_id in channel_ids:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await channel.send(f"Pixelmon data: {pixelmon_data}")
                self.printed_trainers[token_id] = datetime.now()

    @commands.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id in channels:
                await ctx.send(f"{channel.mention} is already a news feed channel.")
                return
            channels.append(channel.id)
            await ctx.send(f"{channel.mention} set as a news feed channel.")

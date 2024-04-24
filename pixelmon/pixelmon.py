from redbot.core import commands, Config
import requests
import logging
import threading
import discord
import asyncio
import time
from datetime import datetime, timedelta

RESERVOIR_API_URL = "https://api.reservoir.tools/orders/asks/v5?tokenSetId=contract%3A0x8a3749936e723325c6b645a0901470cd9e790b94&limit=10"
PIXELMON_API_URL = 'https://api-cp.pixelmon.ai/nft/get-relics-count'

headers = {
    "accept": "*/*",
    "x-api-key": "1d336873-3714-504d-ade9-e0017bc7f390"
}

class Pixelmon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.printed_trainers = {}
        self.config = Config.get_conf(self, identifier=123456789)
        default_guild = {"channels": []}
        self.config.register_guild(**default_guild)
        self.bot.loop.create_task(self.periodic_task())
    
    def cog_unload(self):
        if self.task:
            self.task.cancel()
            self.task = None
        asyncio.create_task(self.session.close())
    
    @commands.group()
    async def pixelmon(self, ctx):
        pass

    async def periodic_task(self):
        while True:
            token_ids = self.fetch_reservoir_data()
            if token_ids:
                self.fetch_pixelmon_data_with_threads(token_ids)
            await asyncio.sleep(30)  # Sleep for 30 seconds before the next iteration

    def fetch_reservoir_data(self):
        try:
            response = requests.get(RESERVOIR_API_URL, headers=headers)
            data = response.json()
            if 'orders' in data:
                return [order['criteria']['data']['token']['tokenId'] for order in data['orders']]
        except Exception as e:
            logging.error(f"Error fetching data from Reservoir API: {e}")
        return None

    def fetch_pixelmon_data(self, trainer_id):
        try:
            payload = {'nftType': 'trainer', 'tokenId': str(trainer_id)}
            response = requests.post(PIXELMON_API_URL, json=payload)
            data = response.json()
            if 'result' in data and 'response' in data['result']:
                relics_response = data['result']['response']['relicsResponse']
                for relic in relics_response:
                    if relic['relicsType'] == 'silver' and relic['count'] > 0:
                        return {'trainer_id': trainer_id, 'relics_count': relic['count']}
        except Exception as e:
            logging.error(f"Error fetching data from Pixelmon API: {e}")
        return None

    def fetch_pixelmon_data_with_threads(self, token_ids):
        threads = []
        for token_id in token_ids:
            thread = threading.Thread(target=self.fetch_and_send_pixelmon_data, args=(token_id,))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

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

    @pixelmon.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id in channels:
                await ctx.send(f"{channel.mention} is already a news feed channel.")
                return
            channels.append(channel.id)
            await ctx.send(f"{channel.mention} set as a news feed channel.")

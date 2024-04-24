import aiohttp
import asyncio
import discord
import logging
import requests
import time
from concurrent.futures import ThreadPoolExecutor

from redbot.core import commands, Config

class Pixelmon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=10000003332)
        default_guild = {"channels": [], "last_message_time": {}}
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()
        self.url_reservoir = "https://api.reservoir.tools/orders/asks/v5?tokenSetId=contract%3A0x8a3749936e723325c6b645a0901470cd9e790b94&limit=10"
        self.url_pixelmon = 'https://api-cp.pixelmon.ai/nft/get-relics-count'
        self.executor = ThreadPoolExecutor(max_workers=5)

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    @commands.group()
    async def pixelmon(self, ctx):
        pass

    @pixelmon.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id not in channels:
                channels.append(channel.id)
                await ctx.send(f"{channel.mention} set as a news feed channel.")
            else:
                await ctx.send(f"{channel.mention} is already a news feed channel.")

    @pixelmon.command()
    async def removechannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id in channels:
                channels.remove(channel.id)
                await ctx.send(f"{channel.mention} removed as a news feed channel.")
            else:
                await ctx.send(f"{channel.mention} is not a news feed channel.")

    @pixelmon.command()
    async def listchannels(self, ctx):
        channels = await self.config.guild(ctx.guild).channels()
        channel_mentions = [f"<#{channel_id}>" for channel_id in channels]
        await ctx.send(f"News feed channels: {', '.join(channel_mentions)}")

    async def fetch_data(self):
        while True:
            try:
                token_ids = self.fetch_reservoir_data()
                if token_ids:
                    self.fetch_pixelmon_data(token_ids)
                await asyncio.sleep(30)  # Run every 30 seconds
            except Exception as e:
                logging.error(f"Error occurred while fetching data: {e}")
                await asyncio.sleep(60)

    def fetch_pixelmon_data(self, token_ids):
        with self.executor as executor:
            future_to_token_id = {executor.submit(self.fetch_pixelmon_data_single, token_id): token_id for token_id in token_ids}
            for future in concurrent.futures.as_completed(future_to_token_id):
                token_id = future_to_token_id[future]
                try:
                    pixelmon_data = future.result()
                    if pixelmon_data and not self.is_message_sent_recently(token_id):
                        self.post_message(pixelmon_data)
                        self.update_last_message_time(token_id)
                except Exception as e:
                    logging.error(f"Error occurred while fetching Pixelmon data for token ID {token_id}: {e}")

    def fetch_pixelmon_data_single(self, token_id):
        try:
            payload = {'nftType': 'pixelmon', 'tokenId': str(token_id)}
            response = requests.post(self.url_pixelmon, json=payload)
            data = response.json()
            if 'result' in data and 'response' in data['result']:
                relics_response = data['result']['response']['relicsResponse']
                for relic in relics_response:
                    if relic['relicsType'] in ['gold', 'diamond'] and relic['count'] > 0:
                        return {
                            'relics_type': relic['relicsType'],
                            'relics_count': relic['count'],
                            'token_id': token_id
                        }
        except Exception as e:
            logging.error(f"Error occurred while fetching data from Pixelmon API for token ID {token_id}: {e}")
        return None

    def fetch_reservoir_data(self):
        try:
            response = requests.get(self.url_reservoir)
            data = response.json()
            if 'orders' in data:
                token_ids = [order['criteria']['data']['token']['tokenId'] for order in data['orders']]
                return token_ids
        except Exception as e:
            logging.error(f"Error occurred while fetching data from Reservoir API: {e}")
        return []

    async def post_message(self, pixelmon_data):
        blur_link = f"https://blur.io/asset/0x8a3749936e723325c6b645a0901470cd9e790b94/{pixelmon_data['token_id']}"
        message = f"@everyone {pixelmon_data['relics_type']} relic count: {pixelmon_data['relics_count']}\n{blur_link}"
        for guild in self.bot.guilds:
            channels = await self.config.guild(guild).channels()
            for channel_id in channels:
                channel = guild.get_channel(channel_id)
                await channel.send(message)

    def is_message_sent_recently(self, token_id):
        last_message_time = self.config.last_message_time(token_id)
        current_time = time.time()
        return current_time - last_message_time < 86400  # 24 hours

    def update_last_message_time(self, token_id):
        current_time = time.time()
        self.config.last_message_time.set_raw(token_id, value=current_time)

from redbot.core import commands, Config
import aiohttp
import asyncio
import discord
import datetime
import pytz
import requests
import logging
import threading
import time

class Pixelmon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=188188188)
        default_guild = {"channels": []}
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()
        self.headers = {
            "accept": "*/*",
            "x-api-key": "1d336873-3714-504d-ade9-e0017bc7f390"
        }
        self.url_reservoir = "https://api.reservoir.tools/orders/asks/v5?tokenSetId=contract%3A0x8a3749936e723325c6b645a0901470cd9e790b94&limit=10"
        self.url_pixelmon = 'https://api-cp.pixelmon.ai/nft/get-relics-count'
        self.url_floor_ask = "https://api.reservoir.tools/events/collections/floor-ask/v2?collection=0x8a3749936e723325c6b645a0901470cd9e790b94&limit=1"
        self.data = []
        self.task = asyncio.create_task(self.fetch_data())
        self.last_message_time = {}

    def cog_unload(self):
        if self.task:
            self.task.cancel()
            self.task = None
        asyncio.create_task(self.session.close())

    @commands.group()
    async def pixelmon(self, ctx):
        pass

    @pixelmon.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id in channels:
                await ctx.send(f"{channel.mention} is already a news feed channel.")
                return
            channels.append(channel.id)
            await ctx.send(f"{channel.mention} set as a news feed channel.")

    @pixelmon.command()
    async def removechannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id not in channels:
                await ctx.send(f"{channel.mention} is not a news feed channel.")
                return
            channels.remove(channel.id)
            await ctx.send(f"{channel.mention} removed as a news feed channel.")

    @pixelmon.command()
    async def listchannels(self, ctx):
        channels = await self.config.guild(ctx.guild).channels()
        if not channels:
            await ctx.send("No news feed channels set.")
            return
        channel_mentions = [f"<#{channel_id}>" for channel_id in channels]
        await ctx.send(f"News feed channels: {', '.join(channel_mentions)}")

    async def fetch_data(self):
        while True:
            try:
                threshold_price = self.get_threshold_price()
                if threshold_price is not None:
                    token_ids = self.fetch_reservoir_data(threshold_price)
                    if token_ids:
                        self.fetch_pixelmon_data_with_threads(token_ids)
                await asyncio.sleep(15)  # Run every 15 seconds
            except Exception as e:
                logging.error(f"Error occurred while fetching data: {e}")
                await asyncio.sleep(60)

    def fetch_pixelmon_data(self, trainer_id):
        try:
            payload = {'nftType': 'trainer', 'tokenId': str(trainer_id)}
            response = requests.post(self.url_pixelmon, json=payload)
            data = response.json()
            if 'result' in data and 'response' in data['result']:
                relics_response = data['result']['response']['relicsResponse']
                for relic in relics_response:
                    if relic['relicsType'] in ['gold', 'diamond'] and relic['count'] > 0:
                        return {
                            'relics_type': relic['relicsType'],
                            'relics_count': relic['count']
                        }
        except Exception as e:
            logging.error(f"Error occurred while fetching data from Pixelmon API: {e}")
        return None

    def fetch_reservoir_data(self, threshold_price):
        try:
            response = requests.get(self.url_reservoir, headers=self.headers)
            data = response.json()
            if 'orders' in data:
                token_ids = []
                for order in data['orders']:
                    # Parse price data
                    price_eth = order['price']['amount']['raw']
                    # Convert to decimal ETH value
                    price_eth_decimal = int(price_eth) / (10 ** 18)
                    token_id = order['criteria']['data']['token']['tokenId']
                    if price_eth_decimal < threshold_price:
                        token_ids.append((token_id, price_eth_decimal))
                return token_ids
        except Exception as e:
            logging.error(f"Error occurred while fetching data from Reservoir API: {e}")
        return None

    def get_threshold_price(self):
        try:
            response = requests.get(self.url_floor_ask, headers=self.headers)
            data = response.json()
            if 'events' in data and data['events']:
                floor_price = data['events'][0]['floorAsk']['price']['amount']['decimal']
                # Add 20% to the floor price
                threshold_price = floor_price * 1.2
                return threshold_price
        except Exception as e:
            logging.error(f"Error occurred while fetching floor price: {e}")
        return None

    def fetch_pixelmon_data_with_threads(self, token_ids):
        loop = asyncio.get_event_loop()
        for token_id, _ in token_ids:
            asyncio.run_coroutine_threadsafe(self.fetch_and_print_pixelmon_data(token_id), loop)
    
    async def fetch_and_print_pixelmon_data(self, token_id):
        pixelmon_data = self.fetch_pixelmon_data(token_id)
        if pixelmon_data:
            # Check if the trainer ID has exceeded the message limit
            if self.check_message_limit(token_id):
                # Construct the OpenSea link with the trainer ID
                blur_link = f"https://blur.io/asset/0x8a3749936e723325c6b645a0901470cd9e790b94/{token_id}"
                message = f"@everyone {pixelmon_data['relics_type']} relic count: {pixelmon_data['relics_count']}\n{blur_link}"
                for guild in self.bot.guilds:
                    channels = await self.config.guild(guild).channels()
                    for channel_id in channels:
                        channel = guild.get_channel(channel_id)
                        await channel.send(message)
                # Update the last message time for the trainer ID
                self.update_last_message_time(token_id)
            else:
                pass
        else:
            pass



    def check_message_limit(self, token_id):
        # Check if the trainer ID has exceeded the message limit (2 messages per hour)
        current_time = time.time()
        last_message_time = self.last_message_time.get(token_id, 0)
        if current_time - last_message_time >= 3600:  # 3600 seconds = 1 hour
            # Reset the message count if the time limit has elapsed
            self.last_message_time[token_id] = current_time
            return True
        else:
            # Check if the message count for the trainer ID exceeds 2
            return self.last_message_time.get(f"{token_id}_count", 0) < 2

    def update_last_message_time(self, token_id):
        # Update the last message time for the trainer ID
        current_time = time.time()
        self.last_message_time[token_id] = current_time
        # Increment the message count for the trainer ID
        self.last_message_time[f"{token_id}_count"] = self.last_message_time.get(f"{token_id}_count", 0) + 1

    def cog_unload(self):
        if self.task:
            self.task.cancel()
            self.task = None
        asyncio.create_task(self.session.close())

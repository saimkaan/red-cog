from redbot.core import commands, Config
import aiohttp
import asyncio
import discord
import requests
import logging
import time

class Trainer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=17171717)
        default_guild = {"channels": []}
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()
        self.headers = {
            "accept": "*/*",
            "x-api-key": "1d336873-3714-504d-ade9-e0017bc7f390"
        }
        self.url_reservoir = "https://api.reservoir.tools/orders/asks/v5?tokenSetId=contract%3A0x8a3749936e723325c6b645a0901470cd9e790b94&limit=10"
        self.url_trainer = 'https://api-cp.pixelmon.ai/nft/get-relics-count'
        self.data = []
        self.task = asyncio.create_task(self.fetch_data())
        self.last_message_time = {}

    def cog_unload(self):
        if self.task:
            self.task.cancel()
            self.task = None
        asyncio.create_task(self.session.close())

    @commands.group()
    async def trainer(self, ctx):
        pass

    @trainer.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id in channels:
                await ctx.send(f"{channel.mention} is already a news feed channel.")
                return
            channels.append(channel.id)
            await ctx.send(f"{channel.mention} set as a news feed channel.")

    @trainer.command()
    async def removechannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id not in channels:
                await ctx.send(f"{channel.mention} is not a news feed channel.")
                return
            channels.remove(channel.id)
            await ctx.send(f"{channel.mention} removed as a news feed channel.")

    @trainer.command()
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
                token_ids = self.fetch_reservoir_data()
                if token_ids:
                    self.fetch_trainer_data_with_threads(token_ids)
                await asyncio.sleep(30)
            except Exception as e:
                logging.error(f"Error occurred while fetching data: {e}")
                await asyncio.sleep(60)

    async def fetch_trainer_data(self, trainer_id):
        try:
            payload = {'nftType': 'trainer', 'tokenId': str(trainer_id)}
            async with self.session.post(self.url_trainer, json=payload) as response:
                data = await response.json()
                if 'result' in data and 'response' in data['result']:
                    gold_relics = None
                    diamond_relics = None
                    relics_response = data['result']['response']['relicsResponse']
                    for relic in relics_response:
                        if relic['relicsType'] == 'diamond' and relic['count'] > 0:
                            diamond_relics = {
                                'relics_type': relic['relicsType'],
                                'relics_count': relic['count']
                            }
                        elif relic['relicsType'] == 'gold' and relic['count'] > 2:
                            gold_relics = {
                                'relics_type': relic['relicsType'],
                                'relics_count': relic['count']
                            }
                    if diamond_relics:
                        return diamond_relics
                    elif gold_relics:
                        return gold_relics
        except Exception as e:
            logging.error(f"Error occurred while fetching data from trainer API: {e}")
        return None


    def fetch_reservoir_data(self):
        try:
            response = requests.get(self.url_reservoir, headers=self.headers)
            data = response.json()
            if 'orders' in data:
                token_data = []
                for order in data['orders']:
                    token_id = order['criteria']['data']['token']['tokenId']
                    decimal_value = order['price']['amount']['decimal']
                    token_data.append({'token_id': token_id, 'decimal_value': decimal_value})
                return token_data
        except Exception as e:
            logging.error(f"Error occurred while fetching data from Reservoir API: {e}")
        return None
    
    async def get_attribute(self, token_id, attribute_key):
        try:
            url = f"https://api.reservoir.tools/collections/0x8a3749936e723325c6b645a0901470cd9e790b94/attributes/explore/v5?tokenId={token_id}&attributeKey={attribute_key}"
            async with self.session.get(url, headers=self.headers) as response:
                data = await response.json()
                if 'attributes' in data and len(data['attributes']) > 0:
                    attributes = data['attributes'][0]
                    if attribute_key == 'floor_price':
                        floor_prices = attributes.get('floorAskPrices', [])
                        if floor_prices:
                            return floor_prices[0]
                    elif attribute_key == 'rarity':
                        return attributes.get('value')
        except Exception as e:
            logging.error(f"Error occurred while fetching {attribute_key}: {e}")
        return None



    def fetch_trainer_data_with_threads(self, token_data):
        loop = asyncio.get_event_loop()
        for data in token_data:
            asyncio.run_coroutine_threadsafe(self.fetch_and_print_trainer_data(data['token_id'], data['decimal_value']), loop)

    async def fetch_and_print_trainer_data(self, token_id, decimal_value):
        trainer_data = await self.fetch_trainer_data(token_id)
        if trainer_data:
            floor_price = await self.get_attribute(token_id, 'floor_price')
            if floor_price is not None and decimal_value > floor_price + 0.08:
                return
            if self.check_message_limit(token_id):
                blur_link = f"https://blur.io/asset/0x8a3749936e723325c6b645a0901470cd9e790b94/{token_id}"
                rarity = await self.get_attribute(token_id, 'rarity')
                if trainer_data['relics_type'] == 'diamond':
                    message = f"@everyone Diamond relic count: {trainer_data['relics_count']}, Rarity: {rarity}, Floor: {floor_price} ETH ---- Current Price: {decimal_value} ETH\n{blur_link}"
                elif trainer_data['relics_type'] == 'gold':
                    message = f"@everyone Gold relic count: {trainer_data['relics_count']}, Rarity: {rarity}, Floor: {floor_price} ETH ---- Current Price: {decimal_value} ETH\n{blur_link}"
                for guild in self.bot.guilds:
                    channels = await self.config.guild(guild).channels()
                    for channel_id in channels:
                        channel = guild.get_channel(channel_id)
                        await channel.send(message)
                self.update_last_message_time(token_id)
            else:
                pass
        else:
            pass

    def check_message_limit(self, token_id):
        current_time = time.time()
        last_message_time = self.last_message_time.get(token_id, 0)
        if current_time - last_message_time >= 86400:
            self.last_message_time[token_id] = current_time
            return True
        else:
            return False

    def update_last_message_time(self, token_id):
        current_time = time.time()
        self.last_message_time[token_id] = current_time
        self.last_message_time[f"{token_id}_count"] = self.last_message_time.get(f"{token_id}_count", 0) + 1

    def cog_unload(self):
        if self.task:
            self.task.cancel()
            self.task = None
        asyncio.create_task(self.session.close())

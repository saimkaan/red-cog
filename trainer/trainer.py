from redbot.core import commands, Config
import aiohttp
import asyncio
import discord
import requests
import logging
import time
import json

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
        self.url_attribute = "https://api.reservoir.tools/collections/0x8a3749936e723325c6b645a0901470cd9e790b94/attributes/explore/v5?tokenId={}&attributeKey=rarity"
        self.data = []
        self.task = asyncio.create_task(self.fetch_data())
        self.last_message_time = {}
        self.last_decimal_values = {}

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
                print("Data from trainer API:", data)  # Add this line to print data
                if 'result' in data and 'response' in data['result']:
                    relics_data = []
                    relics_response = data['result']['response']['relicsResponse']
                    for relic in relics_response:
                        if relic['relicsType'] in ['diamond', 'gold', 'silver', 'bronze', 'wood'] and relic['count'] > 0:
                            relics_data.append({
                                'relics_type': relic['relicsType'],
                                'relics_count': relic['count']
                            })
                    return relics_data
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
        url = self.url_attribute.format(token_id)
        async with self.session.get(url, headers=self.headers) as response:
            data = await response.json()
            if 'attributes' in data and len(data['attributes']) > 0:
                rarity_att = data['attributes'][0]['value']
                floor_price = data['attributes'][0]['floorAskPrices'][0] if 'floorAskPrices' in data['attributes'][0] and len(data['attributes'][0]['floorAskPrices']) > 0 else None
                return rarity_att, floor_price
        return None, None

    async def fetch_trainer_data_with_threads(self, token_data):
        loop = asyncio.get_event_loop()
        for data in token_data:
            relics_data = await self.fetch_trainer_data(data['token_id'])  # Fetch relics data
            if relics_data:  # Check if relics data is not None
                asyncio.run_coroutine_threadsafe(self.fetch_and_print_trainer_data(data['token_id'], data['decimal_value'], relics_data), loop)


    async def fetch_and_print_trainer_data(self, token_id, decimal_value, relics_data):
        total_value = 0
        for relic in relics_data:
            if relic['relics_type'] == 'diamond':
                total_value += relic['relics_count'] * 0.15
            elif relic['relics_type'] == 'gold':
                total_value += relic['relics_count'] * 0.045
            elif relic['relics_type'] == 'silver':
                total_value += relic['relics_count'] * 0.018
            elif relic['relics_type'] == 'bronze':
                total_value += relic['relics_count'] * 0.009
            elif relic['relics_type'] == 'wood':
                total_value += relic['relics_count'] * 0.0024
        
        rarity_att, floor_price = await self.get_attribute(token_id, 'rarity')
        total_value += floor_price
        
        if decimal_value > total_value:
            blur_link = f"https://blur.io/asset/0x8a3749936e723325c6b645a0901470cd9e790b94/{token_id}"
            message = f"@everyone\n"
            for relic in relics_data:
                message += f"{relic['relics_type'].capitalize()} relic count: {relic['relics_count']}\n"
            message += f"{rarity_att} Floor Price + Relic Value: {total_value} ETH\nCurrent Price: {decimal_value} ETH\n{blur_link}"
            
            for guild in self.bot.guilds:
                channels = await self.config.guild(guild).channels()
                for channel_id in channels:
                    channel = guild.get_channel(channel_id)
                    await channel.send(message)


    def cog_unload(self):
        if self.task:
            self.task.cancel()
            self.task = None
        asyncio.create_task(self.session.close())

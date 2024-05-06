from redbot.core import commands, Config
import aiohttp
import asyncio
import discord
import logging
import requests

class TrainerDelay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=2222111)
        default_guild = {"channels": []}
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()
        self.headers = {
            "accept": "*/*",
            "x-api-key": "1d336873-3714-504d-ade9-e0017bc7f390"
        }
        self.url_reservoir = "https://api.reservoir.tools/orders/asks/v5?tokenSetId=contract%3A0x8a3749936e723325c6b645a0901470cd9e790b94&limit=20"
        self.url_trainer = 'https://api-cp.pixelmon.ai/nft/get-relics-count'
        self.url_attribute = "https://api.reservoir.tools/collections/0x8a3749936e723325c6b645a0901470cd9e790b94/attributes/explore/v5?tokenId={}&attributeKey=rarity"
        self.task = asyncio.create_task(self.fetch_data())
        self.last_decimal_values = {}
        self.trainer_cache = {}

    @commands.group()
    async def trainers(self, ctx):
        pass

    @trainers.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id in channels:
                await ctx.send(f"{channel.mention} is already a news feed channel.")
                return
            channels.append(channel.id)
            await ctx.send(f"{channel.mention} set as a news feed channel.")

    @trainers.command()
    async def removechannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id not in channels:
                await ctx.send(f"{channel.mention} is not a news feed channel.")
                return
            channels.remove(channel.id)
            await ctx.send(f"{channel.mention} removed as a news feed channel.")

    @trainers.command()
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
                    await self.fetch_trainer_data_with_threads(token_ids)
                await asyncio.sleep(20)
            except Exception as e:
                logging.error(f"Error occurred while fetching data: {e}")
                await asyncio.sleep(60)

    def fetch_reservoir_data(self):
        try:
            response = requests.get(self.url_reservoir, headers=self.headers)
            data = response.json()
            if 'orders' in data:
                token_data = []
                for order in data['orders']:
                    token_id = order['criteria']['data']['token']['tokenId']
                    decimal_value = order['price']['amount']['decimal']
                    exchange_kind = order['kind']
                    token_data.append({'token_id': token_id, 'decimal_value': decimal_value, 'exchange_kind': exchange_kind})
                return token_data
        except Exception as e:
            logging.error(f"Error occurred while fetching data from Reservoir API: {e}")
        return None

    
    async def fetch_trainer_data_with_threads(self, token_data):
        loop = asyncio.get_event_loop()
        for data in token_data:
            asyncio.run_coroutine_threadsafe(self.fetch_and_print_trainer_data(data['token_id'], data['decimal_value'], data['exchange_kind']), loop)

    async def fetch_and_print_trainer_data(self, token_id, decimal_value, exchange_kind):
        last_decimal_value = self.last_decimal_values.get((token_id, exchange_kind))
        if last_decimal_value is None or last_decimal_value != decimal_value:
            logging.info(f"New message for Trainer token ID {token_id} with decimal value {decimal_value}")
            self.last_decimal_values[(token_id, exchange_kind)] = decimal_value
        else:
            logging.info(f"Message for Trainer token ID {token_id} with decimal value {decimal_value} already posted, skipping.")
        await asyncio.sleep(240)
        if last_decimal_value is None or last_decimal_value != decimal_value:
            trainer_data = await self.fetch_trainer_data(token_id)
            if trainer_data:
                blur_link = f"https://blur.io/asset/0x8a3749936e723325c6b645a0901470cd9e790b94/{token_id}"
                rarity_atts, floor_price = await self.get_attributes(token_id)
                if floor_price is not None:
                    relics_value = self.calculate_relics_value(trainer_data)
                    if relics_value >= 0.15:
                        total_price = floor_price + relics_value
                        relics_info = "\n".join([f"{relic_type.capitalize()} Relic Count: {count}" for relic_type, count in trainer_data.items()])
                        message = f"@everyone\n**{rarity_atts['rarity']}** Trainer: {token_id}\n{relics_info}\nFloor Price: {floor_price:.4f} ETH\nRelics Value: {relics_value:.4f} ETH\n\n**Listing Price: {decimal_value:.4f} ETH**\n{blur_link}"
                        if decimal_value <= total_price:
                            self.last_decimal_values[token_id] = decimal_value
                            for guild in self.bot.guilds:
                                channels = await self.config.guild(guild).channels()
                                for channel_id in channels:
                                    channel = guild.get_channel(channel_id)
                                    allowed_mentions = discord.AllowedMentions(everyone=True)
                                    await channel.send(message, allowed_mentions=allowed_mentions)
            else:
                pass

    async def fetch_trainer_data(self, trainer_id):
        cached_data = self.trainer_cache.get(trainer_id)
        if cached_data:
            return cached_data
        try:
            payload = {'nftType': 'trainer', 'tokenId': str(trainer_id)}
            async with self.session.post(self.url_trainer, json=payload) as response:
                data = await response.json()
                if 'result' in data and 'response' in data['result']:
                    relics_response = data['result']['response']['relicsResponse']
                    relics_data = {}
                    for relic in relics_response:
                        relics_data[relic['relicsType']] = relic['count']
                    self.trainer_cache[trainer_id] = relics_data
                    return relics_data
        except Exception as e:
            logging.error(f"Error occurred while fetching data from trainer API: {e}")
        return None

    async def get_attributes(self, token_id):
        url = self.url_attribute.format(token_id)
        async with self.session.get(url, headers=self.headers) as response:
            data = await response.json()
            if 'attributes' in data and len(data['attributes']) > 0:
                rarity_atts = {attr['key']: attr['value'] for attr in data['attributes']}
                floor_price = data['attributes'][0]['floorAskPrices'][0] if 'floorAskPrices' in data['attributes'][0] and len(data['attributes'][0]['floorAskPrices']) > 0 else None
                return rarity_atts, floor_price
        return None, None

    def calculate_relics_value(self, relics_data):
        relic_values = {'diamond': 0.15, 'gold': 0.045, 'silver': 0.018, 'bronze': 0.009, 'wood': 0.0024, 'unRevealed': 0.0024}
        total_value = 0
        for relic_type, count in relics_data.items():
            if relic_type in relic_values:
                total_value += count * relic_values[relic_type]
        return total_value

    def cog_unload(self):
        if self.task:
            self.task.cancel()
            self.task = None
        asyncio.create_task(self.session.close())
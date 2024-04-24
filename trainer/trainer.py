import aiohttp
import asyncio
import discord
import logging
from redbot.core import commands, Config

class Trainer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=123333123333333)
        default_guild = {"channels": []}
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()
        self.headers = {
            "accept": "*/*",
            "x-api-key": "YOUR_API_KEY"
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
                async with self.session.get(self.url_reservoir, headers=self.headers) as response:
                    data = await response.json()
                    if 'orders' in data:
                        for order in data['orders']:
                            price_eth = order['price']['amount']['raw']
                            price_eth_decimal = int(price_eth) / (10 ** 18)
                            token_id = order['criteria']['data']['token']['tokenId']
                            await self.check_and_post_message(token_id, price_eth_decimal)
            except Exception as e:
                logging.error(f"Error occurred while fetching data: {e}")
            await asyncio.sleep(15)  # Run every 15 seconds

    async def check_and_post_message(self, token_id, price):
        threshold_price = await self.calculate_threshold_price(token_id)
        if threshold_price is not None and price <= threshold_price:
            trainer_data = await self.fetch_trainer_data(token_id)
            if trainer_data:
                message = f"@everyone {trainer_data['relics_type']} relic count: {trainer_data['relics_count']}\n{token_id}"
                for guild in self.bot.guilds:
                    channels = await self.config.guild(guild).channels()
                    for channel_id in channels:
                        channel = guild.get_channel(channel_id)
                        await channel.send(message)

    async def calculate_threshold_price(self, token_id):
        try:
            async with self.session.post(self.url_trainer, json={'nftType': 'trainer', 'tokenId': str(token_id)}) as response:
                data = await response.json()
                if 'result' in data and 'response' in data['result']:
                    relics_response = data['result']['response']['relicsResponse']
                    total_relics_count = sum(relic['count'] for relic in relics_response if relic['relicsType'] in ['gold', 'diamond'])
                    # Adjust threshold based on relics count
                    threshold_price = total_relics_count * 0.15  # 0.15 increase for each relic
                    return threshold_price
        except Exception as e:
            logging.error(f"Error occurred while calculating threshold price: {e}")
        return None

    async def fetch_trainer_data(self, token_id):
        try:
            async with self.session.post(self.url_trainer, json={'nftType': 'trainer', 'tokenId': str(token_id)}) as response:
                data = await response.json()
                if 'result' in data and 'response' in data['result']:
                    relics_response = data['result']['response']['relicsResponse']
                    for relic in relics_response:
                        if relic['relicsType'] in ['gold', 'diamond'] and relic['count'] > 0:
                            return {
                                'relics_type': relic['relicsType'],
                                'relics_count': relic['count']
                            }
        except Exception as e:
            logging.error(f"Error occurred while fetching data from Trainer API: {e}")
        return None

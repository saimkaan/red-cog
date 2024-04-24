from redbot.core import commands, Config
import aiohttp
import asyncio
import discord
import requests
import logging
from datetime import datetime, timedelta

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
        self.url_reservoir = "https://api.reservoir.tools/orders/asks/v5?tokenSetId=contract%3A0x32973908faee0bf825a343000fe412ebe56f802a&limit=10"
        self.url_pixelmon = 'https://api-cp.pixelmon.ai/nft/get-relics-count'
        self.data = []
        self.task = asyncio.create_task(self.fetch_data())
        self.printed_pixelmons = {}

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
                await asyncio.sleep(30)  # Run every 30 seconds
            except Exception as e:
                logging.error(f"Error occurred while fetching data: {e}")
                await asyncio.sleep(60)

    def fetch_pixelmon_data(self, pixelmon_id):
        try:
            payload = {'nftType': 'pixelmon', 'tokenId': str(pixelmon_id)}
            response = requests.post(self.url_pixelmon, json=payload)
            data = response.json()
            if 'result' in data and 'response' in data['result']:
                relics_response = data['result']['response']['relicsResponse']
                for relic in relics_response:
                    if relic['relicsType'] == 'diamond' and relic['count'] > 0:
                        return {
                            'pixelmon_id': pixelmon_id,
                            'relics_count': relic['count']
                        }
        except Exception as e:
            logging.error(f"Error occurred while fetching data from Pixelmon API: {e}")
        return None

    def fetch_reservoir_data(self):
        try:
            response = requests.get(self.url_reservoir, headers=self.headers)
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

    def fetch_pixelmon_data_with_threads(self, token_ids):
        loop = asyncio.get_event_loop()
        for token_id, _ in token_ids:
            asyncio.run_coroutine_threadsafe(self.fetch_and_print_pixelmon_data(token_id), loop)
    
    async def fetch_and_print_pixelmon_data(self, token_id):
        pixelmon_data = self.fetch_pixelmon_data(token_id)
        if pixelmon_data:
            # Check if the pixelmon ID has exceeded the message limit
            if token_id not in self.printed_pixelmons or (datetime.now() - self.printed_pixelmons[token_id]) > timedelta(hours=24):
                # Construct the OpenSea link with the pixelmon ID
                blur_link = f"https://blur.io/asset/0x32973908faee0bf825a343000fe412ebe56f802a/{token_id}"
                message = f"@everyone {pixelmon_data['relics_type']} relic count: {pixelmon_data['relics_count']}\n{blur_link}"
                for guild in self.bot.guilds:
                    channels = await self.config.guild(guild).channels()
                    for channel_id in channels:
                        channel = guild.get_channel(channel_id)
                        await channel.send(message)
                # Update the last message time for the pixelmon ID
                self.printed_pixelmons[token_id] = datetime.now()
            else:
                pass
        else:
            pass

    def cog_unload(self):
        if self.task:
            self.task.cancel()
            self.task = None
        asyncio.create_task(self.session.close())
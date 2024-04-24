import discord
from redbot.core import commands, Config
import aiohttp
import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
import requests

class Pixelmon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1233331233123123)
        default_guild = {"channels": []}
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()
        self.headers = {
            "accept": "*/*",
            "x-api-key": "1d336873-3714-504d-ade9-e0017bc7f390"
        }
        self.RESERVOIR_API_URL = "https://api.reservoir.tools/orders/asks/v5?tokenSetId=contract%3A0x32973908faee0bf825a343000fe412ebe56f802a&limit=10"
        self.PIXELMON_API_URL = 'https://api-cp.pixelmon.ai/nft/get-relics-count'
        self.printed_pixelmons = {}
        self.task = None

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

    async def fetch_reservoir_data(self):
        try:
            response = requests.get(self.RESERVOIR_API_URL, headers=self.headers)
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

    async def fetch_pixelmon_data(self, pixelmon_id):
        try:
            payload = {'nftType': 'pixelmon', 'tokenId': str(pixelmon_id)}
            response = requests.post(self.PIXELMON_API_URL, json=payload)
            data = response.json()
            if 'result' in data and 'response' in data['result']:
                relics_response = data['result']['response']['relicsResponse']
                for relic in relics_response:
                    if relic['relicsType'] == 'wood' and relic['count'] > 0:
                        return {
                            'pixelmon_id': pixelmon_id,
                            'relics_count': relic['count']
                        }
        except Exception as e:
            logging.error(f"Error occurred while fetching data from Pixelmon API: {e}")
        return None

    async def fetch_and_print_pixelmon_data(self, token_id):
        pixelmon_data = await self.fetch_pixelmon_data(token_id)
        if pixelmon_data:
            if token_id not in self.printed_pixelmons or (datetime.now() - self.printed_pixelmons[token_id]) > timedelta(hours=24):
                message = f"Pixelmon data: {pixelmon_data['relics_count']} relics for ID {pixelmon_data['pixelmon_id']}"
                for guild in self.bot.guilds:
                    channels = await self.config.guild(guild).channels()
                    for channel_id in channels:
                        channel = guild.get_channel(channel_id)
                        await channel.send(message)
                self.printed_pixelmons[token_id] = datetime.now()

    async def fetch_pixelmon_data_with_threads(self, token_ids):
        tasks = []
        for token_id in token_ids:
            tasks.append(self.fetch_and_print_pixelmon_data(token_id))
        await asyncio.gather(*tasks)

    async def fetch_data(self):
        while True:
            token_ids = await self.fetch_reservoir_data()
            if token_ids:
                await self.fetch_pixelmon_data_with_threads(token_ids)
            await asyncio.sleep(30)  # Sleep for 30 seconds before the next iteration

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.task:
            self.task = asyncio.create_task(self.fetch_data())

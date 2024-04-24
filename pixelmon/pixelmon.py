import threading
import asyncio
from datetime import datetime, timedelta
import logging
import requests
import discord
from redbot.core import commands, Config

# Define global constants
RESERVOIR_API_URL = "https://api.reservoir.tools/orders/asks/v5?tokenSetId=contract%3A0x32973908faee0bf825a343000fe412ebe56f802a&limit=10"
PIXELMON_API_URL = 'https://api-cp.pixelmon.ai/nft/get-relics-count'

headers = {
    "accept": "*/*",
    "x-api-key": "1d336873-3714-504d-ade9-e0017bc7f390"
}

# Dictionary to store the last printed time for each pixelmon ID
printed_pixelmons = {}

class Pixelmon(commands.Cog):
    async def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=188188188)
        default_guild = {"channels": []}
        self.config.register_guild(**default_guild)
        self.last_message_time = {}

        # Start the main loop
        await self.main_loop()


    def cog_unload(self):
        pass  # No cleanup required for now

    async def main_loop(self):
        while True:
            token_ids = self.fetch_reservoir_data()
            if token_ids:
                self.fetch_pixelmon_data_with_threads(token_ids)
            await asyncio.sleep(30)  # Use asyncio.sleep instead of time.sleep


    def fetch_reservoir_data(self):
        try:
            response = requests.get(RESERVOIR_API_URL, headers=headers)
            data = response.json()
            if 'orders' in data:
                token_ids = [order['criteria']['data']['token']['tokenId'] for order in data['orders']]
                return token_ids
        except Exception as e:
            logging.error(f"Error occurred while fetching data from Reservoir API: {e}")
        return None

    def fetch_pixelmon_data(self, pixelmon_id):
        try:
            payload = {'nftType': 'pixelmon', 'tokenId': str(pixelmon_id)}
            response = requests.post(PIXELMON_API_URL, json=payload)
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

    async def fetch_and_print_pixelmon_data(self, token_id):
        pixelmon_data = self.fetch_pixelmon_data(token_id)
        if pixelmon_data:
            if token_id not in printed_pixelmons or (datetime.now() - printed_pixelmons[token_id]) > timedelta(hours=24):
                blur_link = f"https://blur.io/asset/0x32973908faee0bf825a343000fe412ebe56f802a/{token_id}"
                message = f"DIAMOND RELIC FOUND: {pixelmon_data['pixelmon_id']}: {pixelmon_data['relics_count']}\n{blur_link}"
                for guild in self.bot.guilds:
                    channels = await self.config.guild(guild).channels()
                    for channel_id in channels:
                        channel = guild.get_channel(channel_id)
                        await channel.send(message)
                printed_pixelmons[token_id] = datetime.now()
        else:
            pass  # Handle the case where no data is fetched

    def fetch_pixelmon_data_with_threads(self, token_ids):
        threads = []
        for token_id in token_ids:
            thread = threading.Thread(target=self.fetch_and_print_pixelmon_data, args=(token_id,))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

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

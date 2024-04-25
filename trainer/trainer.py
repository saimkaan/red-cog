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
        self.last_message_time = {}

    def cog_unload(self):
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
                    for token_id in token_ids:
                        await self.fetch_and_print_trainer_data(token_id)
                await asyncio.sleep(30)  # Run every 30 seconds
            except Exception as e:
                logging.error(f"Error occurred while fetching data: {e}")
                await asyncio.sleep(60)

    def fetch_trainer_data(self, trainer_id):
        try:
            payload = {'nftType': 'trainer', 'tokenId': str(trainer_id)}
            response = requests.post(self.url_trainer, json=payload)
            data = response.json()
            if 'result' in data and 'response' in data['result']:
                relics_response = data['result']['response']['relicsResponse']
                for relic in relics_response:
                    if relic['relicsType'] in ['wood', 'diamond'] and relic['count'] > 0:
                        return {
                            'relics_type': relic['relicsType'],
                            'relics_count': relic['count']
                        }
        except Exception as e:
            logging.error(f"Error occurred while fetching data from trainer API: {e}")
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

    async def fetch_and_print_trainer_data(self, token_id):
        trainer_data = self.fetch_trainer_data(token_id)
        if trainer_data:
            # Check if the trainer ID has exceeded the message limit
            if self.check_message_limit(token_id):
                # Construct the OpenSea link with the trainer ID
                blur_link = f"https://blur.io/asset/0x8a3749936e723325c6b645a0901470cd9e790b94/{token_id}"
                relics_message = ""
                for relic_info in trainer_data:
                    relics_message += f"{relic_info['relics_type'].capitalize()}: {relic_info['relics_count']}\n"
                message = f"@everyone Relics count for Trainer {token_id}:\n{relics_message}{blur_link}"
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
        # Check if the trainer ID has exceeded the message limit (1 message per 24 hours)
        current_time = time.time()
        last_message_time = self.last_message_time.get(token_id, 0)
        if current_time - last_message_time >= 86400:  # 86400 seconds = 24 hours
            # Reset the message time if the time limit has elapsed
            self.last_message_time[token_id] = current_time
            return True
        else:
            return False  # Return False to indicate message limit exceeded

    def update_last_message_time(self, token_id):
        # Update the last message time for the trainer ID
        current_time = time.time()
        self.last_message_time[token_id] = current_time
        # Increment the message count for the trainer ID
        self.last_message_time[f"{token_id}_count"] = self.last_message_time.get(f"{token_id}_count", 0) + 1

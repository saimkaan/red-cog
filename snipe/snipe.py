from redbot.core import commands, Config
import aiohttp
import asyncio
import discord
import logging

class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=12344321)
        default_guild = {"channels": []}
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()
        self.headers = {
            "accept": "*/*",
            "x-api-key": "1d336873-3714-504d-ade9-e0017bc7f390"
        }
        self.addresses = [
            "0x8a3749936e723325c6b645a0901470cd9e790b94",
            "0x32973908faee0bf825a343000fe412ebe56f802a"
        ]
        self.url_reservoir = "https://api.reservoir.tools/orders/asks/v5?tokenSetId=contract%3A{address}&limit=20"
        self.data_list = []
        self.task = asyncio.create_task(self.fetch_data_for_addresses())

    @commands.group()
    async def snipe(self, ctx):
        pass

    @snipe.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id in channels:
                await ctx.send(f"{channel.mention} is already a news feed channel.")
                return
            channels.append(channel.id)
            await ctx.send(f"{channel.mention} set as a news feed channel.")

    @snipe.command()
    async def removechannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id not in channels:
                await ctx.send(f"{channel.mention} is not a news feed channel.")
                return
            channels.remove(channel.id)
            await ctx.send(f"{channel.mention} removed as a news feed channel.")

    @snipe.command()
    async def listchannels(self, ctx):
        channels = await self.config.guild(ctx.guild).channels()
        if not channels:
            await ctx.send("No news feed channels set.")
            return
        channel_mentions = [f"<#{channel_id}>" for channel_id in channels]
        await ctx.send(f"News feed channels: {', '.join(channel_mentions)}")
    
    async def fetch_data_for_addresses(self):
        try:
            for address in self.addresses:
                url = self.url_reservoir.format(address=address)
                async with self.session.get(url, headers=self.headers) as response:
                    data = await response.json()
                    for order in data['orders']:
                        token_id = order['criteria']['data']['token']['tokenId']
                        price = order['price']['amount']['decimal']
                        exchange = order['kind']
                        self.data_list.append({"token_id": token_id, "price": price, "exchange": exchange})
            logging.info(f"Fetched data: {self.data_list}")          
        except Exception as e:
            logging.error(f"Error occurred while fetching data from Reservoir API: {e}")

    def cog_unload(self):
        if self.task:
            self.task.cancel()
            self.task = None
        asyncio.create_task(self.session.close())

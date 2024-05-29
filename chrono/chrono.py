from redbot.core import commands, Config
import asyncio
import aiohttp
import discord

class Chrono(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1212555)
        default_guild = {"channels": []}
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()
        self.headers = {
            "accept": "*/*",
            "x-api-key": "60bf8680-7718-50eb-9340-39d85f05cf7d"
        }
        self.processed_orders = {}
        self.contract_address = {
            "chrono": "0x17ed38f5f519c6ed563be6486e629041bed3dfbc",
        }
        self.attribute_traits = ['Second Sight', 'Paralyzing Aura', 'Unbreakable', 'Demonic Strength', 'Shadowborn', 'Flameborn', 'Iceborn', 'Etherbound']
        self.attribute_traits2 = ['Lightning Reflexes', 'Casanova', 'Saintly', 'Taming Touch', 'Unwavering', 'Companion Orb']
        self.task = None

    async def fetch_data(self, session, url):
        async with session.get(url, headers=self.headers) as response:
            return await response.json()

    async def process_order(self, session, token, address, order):
        token_id = order['criteria']['data']['token']['tokenId']
        price = round(order['price']['amount']['decimal'], 2)
        exchange = order['kind']
        if (token_id, price, exchange) in self.processed_orders:
            print(f"Skipping order for token ID {token_id}, price {price}, and exchange {exchange} as it's already processed.")
            return
        self.processed_orders[(token_id, price, exchange)] = True
        attribute_key = "Trait"
        url_attribute = f"https://api.reservoir.tools/collections/{address}/attributes/explore/v5?tokenId={token_id}&attributeKey={attribute_key}"
        attributes_data = await self.fetch_data(session, url_attribute)
        all_traits = [attr['value'] for attr in attributes_data.get('attributes', [])]
        matching_traits = [trait for trait in all_traits if trait in self.attribute_traits]
        matching_traits2 = [trait for trait in all_traits if trait in self.attribute_traits2]

        url_floorprice = f"https://api.reservoir.tools/oracle/collections/floor-ask/v6?collection={address}"
        floorprice_data = await self.fetch_data(session, url_floorprice)
        floorprice = round(floorprice_data.get('price', 'Not available'), 2)
        if floorprice == 'Not available':
            print(f"Floor price not available for token ID {token_id}.")
            return

        if len(matching_traits2) == 2 and floorprice >= price:
            matched_traits_string = ', '.join(matching_traits2)
            blur_link = f"https://blur.io/asset/{address}/{token_id}"
            opensea_link = f"https://pro.opensea.io/nft/ethereum/{address}/{token_id}"
            chrono_link = f"https://chronoforge.gg/adventurer/{token_id}"
            message = f"@everyone\n:blue_circle: **{matched_traits_string}**\n\n**Listing Price: {price} ETH**\n\nChrono: <{chrono_link}>\nOpenSea: <{opensea_link}>\nBlur: {blur_link}"
            for guild in self.bot.guilds:
                channels = await self.config.guild(guild).channels()
                for channel_id in channels:
                    channel = guild.get_channel(channel_id)
                    if channel:
                        allowed_mentions = discord.AllowedMentions(everyone=True)
                        await channel.send(message, allowed_mentions=allowed_mentions)
                    else:
                        print(f"Channel with ID {channel_id} not found in guild {guild.name}.")
        elif matching_traits:
            multiplier = 0.1
            if len(matching_traits) == 2:
                multiplier = 0.2
            if price >= float(floorprice) + multiplier:
                print(f"Price {price} exceeds floor price {floorprice} + {multiplier} for token ID {token_id}.")
                return
            matched_traits_string = ', '.join(matching_traits)
            if matching_traits2:  # Append matching_traits2 if there are any
                matched_traits_string += f" (also includes: :blue_circle: {', '.join(matching_traits2)})"
            blur_link = f"https://blur.io/asset/{address}/{token_id}"
            opensea_link = f"https://pro.opensea.io/nft/ethereum/{address}/{token_id}"
            chrono_link = f"https://chronoforge.gg/adventurer/{token_id}"
            message = f"@everyone\n:purple_circle: **{matched_traits_string}**\n\n**Listing Price: {price} ETH**\n\nChrono: <{chrono_link}>\nOpenSea: <{opensea_link}>\nBlur: {blur_link}"
            for guild in self.bot.guilds:
                channels = await self.config.guild(guild).channels()
                for channel_id in channels:
                    channel = guild.get_channel(channel_id)
                    if channel:
                        allowed_mentions = discord.AllowedMentions(everyone=True)
                        await channel.send(message, allowed_mentions=allowed_mentions)
                    else:
                        print(f"Channel with ID {channel_id} not found in guild {guild.name}.")


    @commands.group()
    async def chrono(self, ctx):
        pass

    @chrono.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id in channels:
                await ctx.send(f"{channel.mention} is already a news feed channel.")
                return
            channels.append(channel.id)
            await ctx.send(f"{channel.mention} set as a news feed channel.")

    @chrono.command()
    async def removechannel(self, ctx, channel: discord.TextChannel):
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id not in channels:
                await ctx.send(f"{channel.mention} is not a news feed channel.")
                return
            channels.remove(channel.id)
            await ctx.send(f"{channel.mention} removed as a news feed channel.")

    @chrono.command()
    async def listchannels(self, ctx):
        channels = await self.config.guild(ctx.guild).channels()
        if not channels:
            await ctx.send("No news feed channels set.")
            return
        channel_mentions = [f"<#{channel_id}>" for channel_id in channels]
        await ctx.send(f"News feed channels: {', '.join(channel_mentions)}")
    
    @chrono.command()
    async def loop(self, ctx, interval: int = 20):
        self.task = asyncio.create_task(self.fetch_orders(ctx, interval))
        await ctx.send("Loop task started.")

    async def fetch_orders(self, ctx, interval):
        async with self.session as session:
            while True:
                try:
                    tasks = []
                    for token, address in self.contract_address.items():
                        url_reservoir = f"https://api.reservoir.tools/orders/asks/v5?tokenSetId=contract%3A{address}&limit=20"
                        data = await self.fetch_data(session, url_reservoir)
                        for order in data['orders']:
                            tasks.append(self.process_order(session, token, address, order))
                    await asyncio.gather(*tasks)
                except Exception as e:
                    print(f"An error occurred: {e}")
                    await asyncio.sleep(interval)
                else:
                    await asyncio.sleep(interval)

    def cog_unload(self):
        if self.task:
            self.task.cancel()
            self.task = None
        asyncio.create_task(self.session.close())

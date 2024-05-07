from redbot.core import commands, Config
import asyncio
import aiohttp
import discord

class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=111222)
        default_guild = {"channels": []}
        self.config.register_guild(**default_guild)
        self.headers = {
            "accept": "*/*",
            "x-api-key": "1d336873-3714-504d-ade9-e0017bc7f390"
        }
        self.relic_values = {'diamond': 0.15, 'gold': 0.045, 'silver': 0.018, 'bronze': 0.009, 'wood': 0.0024, 'unRevealed': 0.0024}
        self.relics_log = {}
        self.contract_address = {
            "trainer": "0x8a3749936e723325c6b645a0901470cd9e790b94",
            "pixelmon": "0x32973908faee0bf825a343000fe412ebe56f802a"
        }

    async def fetch_data(self, session, url):
        async with session.get(url, headers=self.headers) as response:
            return await response.json()

    async def fetch_relics(self, session, url, token, token_id):
        payload = {'nftType': token, 'tokenId': str(token_id)}
        async with session.post(url, json=payload) as response:
            json_data = await response.json()
            return json_data.get('result', {}).get('response', {}).get('relicsResponse', [])

    async def process_order(self, session, token, address, order):
        token_id = order['criteria']['data']['token']['tokenId']
        price = order['price']['amount']['decimal']
        exchange = order['kind']

        attribute_key = "rarity" if token == "trainer" else "Rarity"
        url_attribute = f"https://api.reservoir.tools/collections/{address}/attributes/explore/v5?tokenId={token_id}&attributeKey={attribute_key}"
        attributes_data = await self.fetch_data(session, url_attribute)
        attribute_rarity = attributes_data.get('attributes', [{}])[0].get('value', 'Not available')
        attribute_floorprice = attributes_data.get('attributes', [{}])[0].get('floorAskPrices', [])

        relics_data = self.relics_log.get(token_id)
        if not relics_data:
            url_relics = 'https://api-cp.pixelmon.ai/nft/get-relics-count'
            relics_data = await self.fetch_relics(session, url_relics, token, token_id)
            self.relics_log[token_id] = relics_data

        relics_value = sum(self.relic_values.get(relic.get('relicsType'), 0) * relic.get('count', 0) for relic in relics_data)

        if attribute_floorprice and relics_value >= 0.15:
            floor_price = float(attribute_floorprice[0])
            if floor_price + relics_value >= float(price):
                blur_link = f"https://blur.io/asset/{address}/{token_id}"
                relics_data_str = "\n".join([f"{relic['relicsType'].capitalize()} Relic Count: {relic['count']}" for relic in relics_data])
                message = f"@everyone\n**{attribute_rarity}** Trainer: {token_id}\n{relics_data_str}\nFloor Price: {attribute_floorprice[0]:.4f} ETH\nRelics Value: {relics_value:.4f} ETH\n\n**Listing Price: {price:.4f} ETH**\n{blur_link}"
                for guild in self.bot.guilds:
                                channels = await self.config.guild(guild).channels()
                                for channel_id in channels:
                                    channel = guild.get_channel(channel_id)
                                    allowed_mentions = discord.AllowedMentions(everyone=True)
                                    await channel.send(message, allowed_mentions=allowed_mentions)

    @commands.command()
    async def snipe(self, ctx):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for token, address in self.contract_address.items():
                url_reservoir = f"https://api.reservoir.tools/orders/asks/v5?tokenSetId=contract%3A{address}&limit=20"
                data = await self.fetch_data(session, url_reservoir)
                for order in data['orders']:
                    tasks.append(self.process_order(session, token, address, order))
            await asyncio.gather(*tasks)

from redbot.core import commands
import aiohttp
import discord
import logging

class Relics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.url_relics = 'https://api-cp.pixelmon.ai/nft/get-relics-count'
        self.url_attribute = "https://api.reservoir.tools/collections/{address}/attributes/explore/v5?tokenId={token_id}&attributeKey={attribute_key}"
        self.headers = {
            "accept": "*/*",
            "x-api-key": "1d336873-3714-504d-ade9-e0017bc7f390"
        }
        self.relic_values = {'diamond': 0.15, 'gold': 0.045, 'silver': 0.018, 'bronze': 0.009, 'wood': 0.0024, 'unRevealed': 0.0024}
        self.contract_address = {
            "trainer": "0x8a3749936e723325c6b645a0901470cd9e790b94",
            "pixelmon": "0x32973908faee0bf825a343000fe412ebe56f802a"
        }
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    @commands.group()
    async def relics(self, ctx):
        pass

    @relics.command()
    async def trainer(self, ctx, token_id: int):
        await self.fetch_and_print_relics_data(ctx, token_id, 'trainer')

    @relics.command()
    async def pixelmon(self, ctx, token_id: int):
        await self.fetch_and_print_relics_data(ctx, token_id, 'pixelmon')
    
    @relics.command()
    async def t(self, ctx, token_id: int):
        await self.fetch_and_print_relics_data(ctx, token_id, 'trainer')

    @relics.command()
    async def p(self, ctx, token_id: int):
        await self.fetch_and_print_relics_data(ctx, token_id, 'pixelmon')

    async def fetch_and_print_relics_data(self, ctx, token_id, nft_type):
        relics_data = await self.fetch_relics_data(token_id, nft_type)
        if relics_data:
            address = self.contract_address[nft_type]
            attribute_rarity, attribute_floorprice = await self.fetch_attributes_data(token_id, address, nft_type)
            relics_value = round(sum(self.relic_values.get(relic['relicsType'], 0) * relic['count'] for relic in relics_data), 2)
            if nft_type == 'pixelmon':
                blur_link = f"https://blur.io/asset/0x32973908faee0bf825a343000fe412ebe56f802a/{token_id}"
                opensea_link = f"https://pro.opensea.io/nft/ethereum/0x32973908faee0bf825a343000fe412ebe56f802a/{token_id}"
            else:
                blur_link = f"https://blur.io/asset/0x8a3749936e723325c6b645a0901470cd9e790b94/{token_id}"
                opensea_link = f"https://pro.opensea.io/nft/ethereum/0x8a3749936e723325c6b645a0901470cd9e790b94/{token_id}"
            
            relics_data_str = "\n".join([f"{relic['relicsType'].capitalize()} Relic Count: {relic['count']}" for relic in relics_data])
            floor_price = round(float(attribute_floorprice[0]), 2) if attribute_floorprice else 'N/A'
            message = (
                f"**{attribute_rarity}** {nft_type.capitalize()}: {token_id}\n\n"
                f"{relics_data_str}\n\n"
                f"Floor Price: {floor_price} ETH\n"
                f"Relics Value: {relics_value} ETH\n\n"
                f"OpenSea: <{opensea_link}>\n"
                f"Blur: <{blur_link}>"
            )
            await ctx.send(message)
        else:
            await ctx.send("No data available for the provided token ID.")

    async def fetch_relics_data(self, token_id, nft_type):
        try:
            payload = {'nftType': nft_type, 'tokenId': str(token_id)}
            async with self.session.post(self.url_relics, json=payload) as response:
                data = await response.json()
                if 'result' in data and 'response' in data['result']:
                    return data['result']['response']['relicsResponse']
        except Exception as e:
            logging.error(f"Error occurred while fetching data from relics API: {e}")
        return None

    async def fetch_attributes_data(self, token_id, address, nft_type):
        attribute_key = "rarity" if nft_type == "trainer" else "Rarity"
        url = self.url_attribute.format(address=address, token_id=token_id, attribute_key=attribute_key)
        async with self.session.get(url, headers=self.headers) as response:
            attributes_data = await response.json()
            attributes = attributes_data.get('attributes', [{}])
            attribute_rarity = attributes[0].get('value', 'Not available')
            attribute_floorprice = attributes[0].get('floorAskPrices', [])
            return attribute_rarity, attribute_floorprice

from redbot.core import commands
import requests
import logging

class TrainerRelics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.url_relics = 'https://api-cp.pixelmon.ai/nft/get-relics-count'

    @commands.group()
    async def relics(self, ctx):
        pass

    @relics.command()
    async def trainer(self, ctx, token_id: int):
        await self.fetch_and_print_relics_data(ctx, token_id, 'trainer')

    @relics.command()
    async def pixelmon(self, ctx, token_id: int):
        await self.fetch_and_print_relics_data(ctx, token_id, 'pixelmon')

    async def fetch_and_print_relics_data(self, ctx, token_id, nft_type):
        relics_data = self.fetch_relics_data(token_id, nft_type)
        if relics_data:
            if nft_type == 'pixelmon':
                blur_link = f"https://blur.io/asset/0x32973908faee0bf825a343000fe412ebe56f802a/{token_id}"
            else:
                blur_link = f"https://blur.io/asset/0x8a3749936e723325c6b645a0901470cd9e790b94/{token_id}"
            relics_message = "\n".join([f"{relic['relicsType']} relic count: {relic['count']}" for relic in relics_data['relics']])
            message = f"{relics_message}\n{blur_link}"
            await ctx.send(message)
        else:
            await ctx.send("No data available for the provided token ID.")

    def fetch_relics_data(self, token_id, nft_type):
        try:
            payload = {'nftType': nft_type, 'tokenId': str(token_id)}
            response = requests.post(self.url_relics, json=payload)
            data = response.json()
            if 'result' in data and 'response' in data['result']:
                relics_response = data['result']['response']['relicsResponse']
                relics = []
                for relic in relics_response:
                    relics.append({
                        'relicsType': relic['relicsType'],
                        'count': relic['count']
                    })
                return {'relics': relics}
        except Exception as e:
            logging.error(f"Error occurred while fetching data from relics API: {e}")
        return None

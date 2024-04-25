from redbot.core import commands
import requests
import logging

class TrainerRelics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.url_trainer = 'https://api-cp.pixelmon.ai/nft/get-relics-count'

    @commands.group()
    async def trainerrelics(self, ctx):
        pass

    @trainerrelics.command()
    async def get(self, ctx, token_id: int):
        await self.fetch_and_print_trainerrelics_data(ctx, token_id)

    async def fetch_and_print_trainerrelics_data(self, ctx, token_id):
        trainerrelics_data = self.fetch_trainerrelics_data(token_id)
        if trainerrelics_data:
            blur_link = f"https://blur.io/asset/0x8a3749936e723325c6b645a0901470cd9e790b94/{token_id}"
            message = f"{trainerrelics_data['relics_type']} relic count: {trainerrelics_data['relics_count']}\n{blur_link}"
            await ctx.send(message)
        else:
            await ctx.send("No data available for the provided token ID.")

    def fetch_trainerrelics_data(self, trainerrelics_id):
        try:
            payload = {'nftType': 'trainer', 'tokenId': str(trainerrelics_id)}
            response = requests.post(self.url_trainer, json=payload)
            data = response.json()
            if 'result' in data and 'response' in data['result']:
                relics_response = data['result']['response']['relicsResponse']
                for relic in relics_response:
                    if relic['relicsType'] == 'diamond':
                        return {
                            'relics_type': relic['relicsType'],
                            'relics_count': relic['count']
                        }
        except Exception as e:
            logging.error(f"Error occurred while fetching data from trainerrelics API: {e}")
        return None

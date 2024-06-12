from redbot.core import commands
import requests
import logging
from web3 import Web3

class Mon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.url_points = 'https://api-staking.monprotocol.ai/points/'

    @commands.group()
    async def mon(self, ctx):
        """Commands related to Mon Protocol data."""
        pass

    @mon.command()
    async def points(self, ctx, address: str):
        """Fetches and displays points data for a given Ethereum address."""
        try:
            to_block = await self.get_current_block()
            if to_block is None:
                await ctx.send("Failed to fetch current block number.")
                return

            data = self.fetch_points_data(address, to_block)
            if data:
                message = (
                    f"Total Burned: {data.get('totalBurned', 0)}\n"
                    f"Current Points: {data.get('netPoints', 0)}\n"
                    f"Staked MON: {data.get('rate', 0)}\n"
                    f"Multiplier: {data.get('multiplier', 0)}"
                )
                await ctx.send(message)
            else:
                await ctx.send("No data available for the provided address.")
        except Exception as e:
            logging.error(f"Error occurred while fetching points data: {e}")
            await ctx.send("An error occurred while fetching data from Mon Protocol API.")

    async def get_current_block(self):
        try:
            # Replace with your Ethereum node URL or Infura project ID
            w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/your_infura_project_id'))
            return w3.eth.block_number
        except Exception as e:
            logging.error(f"Error occurred while fetching current block number: {e}")
            return None

    def fetch_points_data(self, address, to_block):
        try:
            url = f"{self.url_points}{address}?toBlock={to_block}"
            headers = {
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9,de;q=0.8",
                "sec-ch-ua": "\"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Failed to fetch data from Mon Protocol API. Status code: {response.status_code}")
        except Exception as e:
            logging.error(f"Error occurred while fetching data from Mon Protocol API: {e}")
        return None
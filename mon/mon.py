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
        to_block = await self.get_current_block()
        data = self.fetch_points_data(address, to_block)
        if data:
            total_burned_sum = data.get("totalBurnedSum", 0)
            total_net_sum = data.get("totalNetSum", 0)
            total_rate_sum = data.get("totalRateSum", 0)

            message = (
                f"Total Burned Sum: {total_burned_sum}\n"
                f"Total Net Sum: {total_net_sum}\n"
                f"Total Rate Sum: {total_rate_sum}"
            )
            await ctx.send(message)
        else:
            await ctx.send("Failed to fetch data from Mon Protocol API.")

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
                data = response.json()
                total_burned_sum = data.get("totalBurned", 0)
                total_net_sum = data.get("netPoints", 0)
                total_rate_sum = data.get("rate", 0)
                return {
                    "totalBurnedSum": total_burned_sum,
                    "totalNetSum": total_net_sum,
                    "totalRateSum": total_rate_sum
                }
            else:
                logging.error(f"Failed to fetch data from Mon Protocol API. Status code: {response.status_code}")
        except Exception as e:
            logging.error(f"Error occurred while fetching data from Mon Protocol API: {e}")
        return None
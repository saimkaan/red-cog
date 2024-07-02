from redbot.core import commands
import requests
from tabulate import tabulate

class Arb(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.contract_addresses = {
            "trainer": "0x8a3749936e723325c6b645a0901470cd9e790b94",
            "pixelmon": "0x32973908faee0bf825a343000fe412ebe56f802a",
            "e2": "0x32973908faee0bf825a343000fe412ebe56f802a"  # Add the e2 contract address here
        }
        self.reservoir_api_key = "60bf8680-7718-50eb-9340-39d85f05cf7d"
        self.coinmarketcap_api_key = "a4a8acd9-732c-4857-8d86-5b1e620572b9"
        self.mon_locked_amounts_pixelmon = {
            "Common": 9058,
            "Uncommon": 9964,
            "Rare": 10870,
            "Epic": 14493,
            "Legendary": 27175,
            "Mythical": 135878
        }
        self.mon_locked_amounts_trainers = {
            "Golden": 130000,
            "mythic": 27175,
            "Mythic": 27175,
            "Legendary": 5435,
            "Epic": 2898,
            "Rare": 2174,
            "Uncommon": 1992,
            "Common": 1811
        }
        self.mon_locked_amounts_e2 = {
            "Common": 10870,
            "Uncommon": 11957,
            "Rare": 13044,
            "Epic": 17392,
            "Legendary": 32610,
            "Mythical": 163054
        }
        self.mon_price_usd = self.get_crypto_price("MON")
        self.eth_price_usd = self.get_crypto_price("ETH")

    def fetch_nft_data(self, contract_name, contract_address):
        url = f"https://api.reservoir.tools/collections/{contract_address}/attributes/explore/v5?attributeKey={'rarity' if contract_name == 'trainer' else 'Rarity'}"
        headers = {
            "accept": "*/*",
            "x-api-key": self.reservoir_api_key
        }
        response = requests.get(url, headers=headers)
        nft_data = response.json()
        return nft_data

    def get_crypto_price(self, symbol):
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        params = {
            "symbol": symbol,
            "convert": "USD"
        }
        headers = {
            "X-CMC_PRO_API_KEY": self.coinmarketcap_api_key
        }
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        return data["data"][symbol]["quote"]["USD"]["price"]

    async def fetch_and_print_data(self, ctx, contract_name):
        contract_address = self.contract_addresses.get(contract_name)
        if not contract_address:
            await ctx.send(f"Contract {contract_name} not found.")
            return

        nft_data = self.fetch_nft_data(contract_name, contract_address)

        rarities = []
        mon_locked_usd = []
        mon_value_usd_list = []
        discounts_usd = []
        discounts_pct = []

        mon_locked_amounts = (
            self.mon_locked_amounts_trainers if contract_name == "trainer"
            else self.mon_locked_amounts_pixelmon if contract_name == "pixelmon"
            else self.mon_locked_amounts_e2 if contract_name == "e2"
            else {}
        )

        for attribute in nft_data['attributes']:
            rarity = attribute['value']

            if rarity == 'Unknown':
                continue

            floor_ask_price_eth = attribute['floorAskPrices'][0]
            floor_ask_price_usd = floor_ask_price_eth * self.eth_price_usd

            if floor_ask_price_usd == 0.00:
                continue

            mon_locked_amount = mon_locked_amounts.get(rarity, 0)
            mon_bought_with_floor_price = floor_ask_price_usd / self.mon_price_usd
            discount_usd = mon_locked_amount - mon_bought_with_floor_price
            discount_pct = (discount_usd / mon_bought_with_floor_price) * 100 if mon_bought_with_floor_price else 0

            rarities.append(rarity)
            mon_locked_usd.append(mon_locked_amount)
            mon_value_usd_list.append(mon_bought_with_floor_price)
            discounts_usd.append(discount_usd)
            discounts_pct.append(discount_pct)

        table_data = []
        for i in range(len(rarities)):
            table_data.append([rarities[i], mon_locked_usd[i], mon_value_usd_list[i], discounts_usd[i], discounts_pct[i]])

        output_table = tabulate(table_data, headers=["Rarity", "Mon Locked", "Mon Equivalent", "Discount (MON)", "Discount (%)"])
        await ctx.send(f"Contract: {contract_name} ({contract_address})\n```\n{output_table}\n```")

    @commands.group()
    async def arb(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @arb.command()
    async def trainer(self, ctx: int):
        await self.fetch_and_print_data(ctx, 'trainer')

    @arb.command()
    async def pixelmon(self, ctx: int):
        await self.fetch_and_print_data(ctx, 'pixelmon')

    @arb.command()
    async def e2(self, ctx: int):
        await self.fetch_and_print_data(ctx, 'e2')

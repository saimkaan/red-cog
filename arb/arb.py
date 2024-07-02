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
        self.species_rarity_map = {
            "Antonne": "Common",
            "Arachneae": "Common",
            "Bloopius": "Common",
            "Boodecept": "Common",
            "Bruizton": "Common",
            "Bugglebug": "Common",
            "Bullmore": "Common",
            "Cheblammo": "Common",
            "Cubixear": "Common",
            "Drootle": "Common",
            "Fowlian": "Common",
            "Haptorid": "Common",
            "Hazerduz": "Common",
            "Bellowhound": "Common",
            "Piu-2": "Common",
            "Shelkjet": "Common",
            "Spoutcrest": "Common",
            "Tookem": "Common",
            "Flowuff": "Common",
            "Xanshadow": "Common",
            "Brawlot": "Uncommon",
            "Cactwodom": "Uncommon",
            "Flickhorn": "Uncommon",
            "Foxetacean": "Uncommon",
            "Metascan": "Uncommon",
            "Molebore": "Uncommon",
            "Nethratine": "Uncommon",
            "Sharpearl": "Uncommon",
            "Uiop": "Uncommon",
            "Lilamoth": "Uncommon",
            "Sharmendu": "Uncommon",
            "Sheedlax": "Uncommon",
            "Wardenon": "Uncommon",
            "Aquahond": "Rare",
            "Apamon": "Rare",
            "Fiveticles": "Rare",
            "Goloidon": "Rare",
            "Embercowl": "Rare",
            "Hubb-L/C": "Rare",
            "Inferknight": "Rare",
            "Lunaful": "Rare",
            "Octopodus": "Rare",
            "Pinmeleon": "Rare",
            "R7n3-B": "Rare",
            "Rahvager": "Rare",
            "Bergum": "Epic",
            "Borgol": "Epic",
            "Floratopsian": "Epic",
            "Harrow": "Epic",
            "Cephaqueen": "Epic",
            "Krawarrior": "Epic",
            "Marrohowl": "Epic",
            "Mr.mask": "Epic",
            "Purralycat": "Epic",
            "Slythiss": "Epic",
            "Repteg": "Legendary",
            "Bengusi": "Legendary",
            "Ardentrus": "Legendary",
            "Grailshield": "Legendary",
            "T.r.b.y.n": "Legendary",
            "Primeonimbus": "Legendary",
            "Serdrake": "Legendary",
            "Xyvonna": "Legendary",
            "Titanoth": "Mythical",
            "Aonithan": "Mythical",
            "Hariken": "Mythical",
            "Ferrunos": "Mythical"
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

    def fetch_e2_floor_prices(self):
        url = "https://api.reservoir.tools/collections/0x32973908faee0bf825a343000fe412ebe56f802a/attributes/explore/v5?attributeKey=Species&limit=200"
        headers = {
            "accept": "*/*",
            "x-api-key": self.reservoir_api_key
        }
        response = requests.get(url, headers=headers)
        nft_data = response.json()

        e2_lowest_prices = {
            "Common": float('inf'),
            "Uncommon": float('inf'),
            "Rare": float('inf'),
            "Epic": float('inf'),
            "Legendary": float('inf'),
            "Mythical": float('inf')
        }

        for attribute in nft_data['attributes']:
            species = attribute['value']
            rarity = self.species_rarity_map.get(species)

            if rarity == 'Unknown' or rarity is None:
                continue

            floor_ask_prices = attribute['floorAskPrices']
            if rarity in e2_lowest_prices:
                min_price = min(floor_ask_prices)
                if min_price < e2_lowest_prices[rarity]:
                    e2_lowest_prices[rarity] = min_price

        return e2_lowest_prices

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

        if contract_name == "e2":
            # Fetch lowest floorAskPrices from e2 API
            e2_prices = self.fetch_e2_floor_prices()

        for attribute in nft_data['attributes']:
            rarity = attribute['value']

            if rarity == 'Unknown':
                continue

            floor_ask_price_eth = e2_prices.get(rarity, 0) if contract_name == "e2" else attribute['floorAskPrices'][0]
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

        table_data = {
            "Rarity": rarities,
            "MON_locked ($)": mon_locked_usd,
            "MON_bought ($)": mon_value_usd_list,
            "Discount ($)": discounts_usd,
            "Discount (%)": discounts_pct
        }

        table = tabulate(table_data, headers="keys", tablefmt="fancy_grid")

        await ctx.send(f"```{table}```")

    @commands.command()
    async def pixelmon(self, ctx):
        await self.fetch_and_print_data(ctx, "pixelmon")

    @commands.command()
    async def trainer(self, ctx):
        await self.fetch_and_print_data(ctx, "trainer")

    @commands.command()
    async def e2(self, ctx):
        await self.fetch_and_print_data(ctx, "e2")

def setup(bot):
    bot.add_cog(Arb(bot))

from redbot.core import commands
import requests
from tabulate import tabulate

class Arb(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.contract_addresses = {
            "trainer": "0x8a3749936e723325c6b645a0901470cd9e790b94",
            "pixelmon": "0x32973908faee0bf825a343000fe412ebe56f802a",
            "pixelmon-e2": "0x32973908faee0bf825a343000fe412ebe56f802a"
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
        self.mon_locked_amounts_pixelmon_e2 = {
            "Common": 10870,
            "Uncommon": 11957,
            "Rare": 13044,
            "Epic": 17392,
            "Legendary": 32610,
            "Mythical": 163054
        }
        self.mon_price_usd = self.get_crypto_price("MON")
        self.eth_price_usd = self.get_crypto_price("ETH")

        self.commonSpecies = [
            "Antonne", "Arachneae", "Bloopius", "Boodecept", "Bruizton",
            "Bugglebug", "Bullmore", "Cheblammo", "Cubixear", "Drootle",
            "Fowlian", "Haptorid", "Hazerduz", "Bellowhound", "Piu-2",
            "Shelkjet", "Spoutcrest", "Tookem", "Flowuff", "Xanshadow"
        ]

        self.uncommonSpecies = [
            "Brawlot", "Cactwodom", "Flickhorn", "Foxetacean", "Metascan",
            "Molebore", "Nethratine", "Sharpearl", "Uiop", "Lilamoth",
            "Sharmendu", "Sheedlax", "Wardenon"
        ]

        self.rareSpecies = [
            "Aquahond", "Apamon", "Fiveticles", "Goloidon", "Embercowl",
            "Hubb-L/C", "Inferknight", "Lunaful", "Octopodus", "Pinmeleon",
            "R7n3-B", "Rahvager"
        ]

        self.epicSpecies = [
            "Bergum", "Borgol", "Floratopsian", "Harrow", "Cephaqueen",
            "Krawarrior", "Marrohowl", "Mr.mask", "Purralycat", "Slythiss"
        ]

        self.legendarySpecies = [
            "Repteg", "Bengusi", "Ardentrus", "Grailshield", "T.r.b.y.n",
            "Primeonimbus", "Serdrake", "Xyvonna"
        ]

        self.mythicalSpecies = [
            "Titanoth", "Aonithan", "Hariken", "Ferrunos"
        ]

    def fetch_nft_data(self, contract_name, contract_address):
        if contract_name == 'trainer':
            attribute_key = 'rarity'
        elif contract_name == 'pixelmon-e2':
            attribute_key = 'Species'
        else:
            attribute_key = 'Rarity'
        
        url = f"https://api.reservoir.tools/collections/{contract_address}/attributes/explore/v5?attributeKey={attribute_key}"
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

    def calculate_lowest_floor_prices(self, species_data):
        lowest_prices = {
            'Common': float('inf'),
            'Uncommon': float('inf'),
            'Rare': float('inf'),
            'Epic': float('inf'),
            'Legendary': float('inf'),
            'Mythical': float('inf')
        }

        if not species_data:
            return lowest_prices

        for species in species_data['attributes']:
            species_name = species.get('value', {}).get('Species', '')
            floor_ask_price = species.get('value', {}).get('FloorAskPrice', 0)

            if species_name in self.commonSpecies:
                lowest_prices['Common'] = min(lowest_prices['Common'], floor_ask_price)
            elif species_name in self.uncommonSpecies:
                lowest_prices['Uncommon'] = min(lowest_prices['Uncommon'], floor_ask_price)
            elif species_name in self.rareSpecies:
                lowest_prices['Rare'] = min(lowest_prices['Rare'], floor_ask_price)
            elif species_name in self.epicSpecies:
                lowest_prices['Epic'] = min(lowest_prices['Epic'], floor_ask_price)
            elif species_name in self.legendarySpecies:
                lowest_prices['Legendary'] = min(lowest_prices['Legendary'], floor_ask_price)
            elif species_name in self.mythicalSpecies:
                lowest_prices['Mythical'] = min(lowest_prices['Mythical'], floor_ask_price)

        return lowest_prices

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

        if contract_name == "trainer":
            mon_locked_amounts = self.mon_locked_amounts_trainers
        elif contract_name == "pixelmon":
            mon_locked_amounts = self.mon_locked_amounts_pixelmon
        elif contract_name == "pixelmon-e2":
            mon_locked_amounts = self.mon_locked_amounts_pixelmon_e2
        else:
            mon_locked_amounts = {}

        lowest_floor_prices = self.calculate_lowest_floor_prices(nft_data)

        for rarity in lowest_floor_prices:
            floor_ask_price_usd = lowest_floor_prices[rarity]
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
    async def pixelmon_e2(self, ctx: int):
        await self.fetch_and_print_data(ctx, 'pixelmon-e2')

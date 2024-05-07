import asyncio
import aiohttp

contract_address = {
    "trainer": "0x8a3749936e723325c6b645a0901470cd9e790b94",
    "pixelmon": "0x32973908faee0bf825a343000fe412ebe56f802a"
}

headers = {
    "accept": "*/*",
    "x-api-key": "1d336873-3714-504d-ade9-e0017bc7f390"
}

relic_values = {'diamond': 0.15, 'gold': 0.045, 'silver': 0.018, 'bronze': 0.009, 'wood': 0.0024, 'unRevealed': 0.0024}
relics_log = {}

async def fetch_data(session, url):
    async with session.get(url, headers=headers) as response:
        return await response.json()

async def fetch_relics(session, url, token, token_id):
    payload = {'nftType': token, 'tokenId': str(token_id)}
    async with session.post(url, json=payload) as response:
        json_data = await response.json()
        return json_data.get('result', {}).get('response', {}).get('relicsResponse', [])

async def process_order(session, token, address, order):
    token_id = order['criteria']['data']['token']['tokenId']
    price = order['price']['amount']['decimal']
    exchange = order['kind']

    attribute_key = "rarity" if token == "trainer" else "Rarity"
    url_attribute = f"https://api.reservoir.tools/collections/{address}/attributes/explore/v5?tokenId={token_id}&attributeKey={attribute_key}"
    attributes_data = await fetch_data(session, url_attribute)
    attribute_rarity = attributes_data.get('attributes', [{}])[0].get('value', 'Not available')
    attribute_floorprice = attributes_data.get('attributes', [{}])[0].get('floorAskPrices', [])

    relics_data = relics_log.get(token_id)
    if not relics_data:
        url_relics = 'https://api-cp.pixelmon.ai/nft/get-relics-count'
        relics_data = await fetch_relics(session, url_relics, token, token_id)
        relics_log[token_id] = relics_data

    relics_value = sum(relic_values.get(relic.get('relicsType'), 0) * relic.get('count', 0) for relic in relics_data)

    if attribute_floorprice and relics_value >= 0.15:
        floor_price = float(attribute_floorprice[0])
        if floor_price + relics_value >= float(price):
            print("Token:", token)
            print("Token ID:", token_id)
            print("Price:", price)
            print("Exchange:", exchange)
            print("Rarity:", attribute_rarity)
            print("Floor Price:", attribute_floorprice)
            print("Relics Count:", relics_data)
            print("Total Relics Value:", relics_value)
            print("Great Deal!!!")
            print("-------------------------")

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for token, address in contract_address.items():
            url_reservoir = f"https://api.reservoir.tools/orders/asks/v5?tokenSetId=contract%3A{address}&limit=20"
            data = await fetch_data(session, url_reservoir)
            for order in data['orders']:
                tasks.append(process_order(session, token, address, order))
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())

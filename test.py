import requests

contract_address = {
    "trainer": "0x32973908faee0bf825a343000fe412ebe56f802a",
    "pixelmon": "0x8a3749936e723325c6b645a0901470cd9e790b94"
}

headers = {
    "accept": "*/*",
    "x-api-key": "1d336873-3714-504d-ade9-e0017bc7f390"
}

for token, address in contract_address.items():
    url = f"https://api.reservoir.tools/orders/asks/v5?tokenSetId=contract%3A{address}&limit=2"
    response = requests.get(url, headers=headers)
    data = response.json()

    print("Token:", token)
    for order in data['orders']:
        token_id = order['criteria']['data']['token']['tokenId']
        price = order['price']['amount']['decimal']
        exchange = order['kind']
        print("Token ID:", token_id)
        print("Price:", price)
        print("Exchange:", exchange)

        # Fetch url_attribute API
        if token == "pixelmon":
            attribute_key = "rarity"
        elif token == "trainer":
            attribute_key = "Rarity"
        url_attribute = f"https://api.reservoir.tools/collections/{address}/attributes/explore/v5?tokenId={token_id}&attributeKey={attribute_key}"
        response_attribute = requests.get(url_attribute, headers=headers)
        attributes_data = response_attribute.json().get('attributes', [])
        if attributes_data:
            attribute_rarity = attributes_data[0]['value']
            attribute_floorprice = attributes_data[0].get('floorAskPrices', 'Not available')
            print("Rarity:", attribute_rarity)
            print("Floor Price:", attribute_floorprice)
        else:
            print("Attribute Value: Not available")

        # Fetch url_relics API
        url_relics = 'https://api-cp.pixelmon.ai/nft/get-relics-count'
        payload = {'nftType': token, 'tokenId': str(token_id)}
        response_relics = requests.post(url_relics, json=payload)
        relics_data = response_relics.json().get('result', {}).get('response', {}).get('relicsResponse', [])
        if relics_data:
            print("Relics Count:")
            for relic in relics_data:
                print(f"{relic['relicsType']}: {relic['count']}")
        else:
            print("Relics Count: Not available")

        print("-------------------------")

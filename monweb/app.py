from flask import Flask, request, render_template
import requests
from web3 import Web3
import threading
import time
import logging

app = Flask(__name__)

URL_POINTS = 'https://api-staking.monprotocol.ai/points/'
ETH_NODE_URL = 'https://mainnet.infura.io/v3/7d62829be3c249afa81cec1cb5681c89'

# Define preset addresses with custom names
PRESET_ADDRESSES = [
    {'address': '0x5af7875766d1a50d144df63e581c0764f6573487', 'name': 'GRAIL'},
    {'address': '0x5c7bcc8af1435e69456e1d25d7fdf569a044a4b4', 'name': 'GRAIL'},
    {'address': '0x044c8f54235e5293db95ac58ac6155578b8a695e', 'name': 'KONGER'},
    {'address': '0x2ab7c08c7b5522a565b5d3be916f546e998aae64', 'name': '???'},
    {'address': '0x63d4fa0f6000ba9ede12be6cd081e443571ad939', 'name': 'ICEDCOFFEE'},
    {'address': '0x90e547bf19323bab9993b04a408d983a4c2a0b66', 'name': 'SCOTTY'},
    {'address': '0xd7803c57551eb36f98d4ec7bfe57ac03dbb5b833', 'name': '???'},
    {'address': '0xd978f8a18b15262f965bf83eaa91de028fe8747f', 'name': 'CAFER'},
    {'address': '0xc5c4980c6a18560f048b76883ad60db67570d892', 'name': 'BITROX'},
    {'address': '0xd6e16c2dba8e506538b11c54b55aaec2bb1f23a0', 'name': '???'}
]

w3 = Web3(Web3.HTTPProvider(ETH_NODE_URL))

def get_current_block():
    try:
        return w3.eth.block_number
    except Exception as e:
        logging.error(f"Error occurred while fetching current block number: {e}")
        return None

def fetch_points_data(address, to_block):
    try:
        url = f"{URL_POINTS}{address}?toBlock={to_block}"
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
        logging.info(f"Fetching data from URL: {url}")
        response = requests.get(url, headers=headers)
        logging.info(f"Response Status Code: {response.status_code}")
        logging.info(f"Response Content: {response.content}")
        if response.status_code == 200:
            data = response.json()
            return {
                "totalBurned": data.get("totalBurned", 0),
                "netPoints": data.get("netPoints", 0),
                "rate": data.get("rate", 0),
                "multiplier": data.get("multiplier", 0)
            }
        else:
            logging.error(f"Failed to fetch data from Mon Protocol API. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error occurred while fetching data from Mon Protocol API: {e}")
    return None

def update_preset_wallets():
    while True:
        to_block = get_current_block()
        if to_block:
            new_preset_data = []
            for wallet in PRESET_ADDRESSES:
                address = wallet['address']
                name = wallet['name']
                new_data = fetch_points_data(address, to_block)
                if new_data:
                    new_wallet_data = {
                        'name': name,
                        'address': address,
                        'totalBurned': new_data.get('totalBurned', 0),
                        'netPoints': new_data.get('netPoints', 0),
                        'rate': new_data.get('rate', 0),
                        'multiplier': new_data.get('multiplier', 0)
                    }
                    new_preset_data.append(new_wallet_data)

            global preset_wallets
            global last_updated_data
            if not preset_wallets:
                preset_wallets = new_preset_data
            else:
                for new_wallet_data in new_preset_data:
                    for old_wallet_data in preset_wallets:
                        if new_wallet_data['address'] == old_wallet_data['address']:
                            if new_wallet_data['totalBurned'] != old_wallet_data['totalBurned'] or \
                               new_wallet_data['netPoints'] != old_wallet_data['netPoints'] or \
                               new_wallet_data['rate'] != old_wallet_data['rate'] or \
                               new_wallet_data['multiplier'] != old_wallet_data['multiplier']:
                                last_updated_data[new_wallet_data['address']] = old_wallet_data
                                break

            preset_wallets = new_preset_data
        time.sleep(1800)  # Wait for 30 minutes

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    changed_data = None
    if request.method == 'POST':
        address = request.form['address']
        to_block = get_current_block()
        if to_block:
            data = fetch_points_data(address, to_block)
            if data:
                result = {
                    'address': address,
                    'totalBurned': data.get('totalBurned', 0),
                    'netPoints': data.get('netPoints', 0),
                    'rate': data.get('rate', 0),
                    'multiplier': data.get('multiplier', 0)
                }
    global last_updated_data
    if last_updated_data:
        changed_data = {address: {
            'previous_totalBurned': last_updated_data[address]['totalBurned'],
            'previous_netPoints': last_updated_data[address]['netPoints'],
            'previous_rate': last_updated_data[address]['rate'],
            'previous_multiplier': last_updated_data[address]['multiplier']
        } for address in last_updated_data}
    return render_template('index.html', result=result, preset_wallets=preset_wallets, changed_data=changed_data)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    preset_wallets = []
    last_updated_data = {}
    threading.Thread(target=update_preset_wallets, daemon=True).start()
    app.run(host='0.0.0.0', port=80)

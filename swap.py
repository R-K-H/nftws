#!/usr/bin/env python
# coding: utf-8

# In[1]:


import math
import time

import requests
import ujson

# In[2]:


ui_url = "https://www.treasureland.market/assets"
api_url = "https://api.treasureland.market/v2/v1"
nft_api_url = "https://api.treasureland.market/v2/v1/nft/"
params = "items?chain_id=56&page_no=1"
chain_id = 56
limit = 1000
bunnies_collection_contract = "0xdf7952b35f24acf7fc0487d01c8d5690a60dba07"
# Total NFTs: 408549
bunnies = {
    "Swapsies": {
        "id": 0,
        "total_count": 112,
        "total_burned": 63,
    },
    "Drizzle": {
        "id": 1,
        "total_count": 101,
        "total_burned": 16,
    },
    "Blueberries": {
        "id": 2,
        "total_count": 74,
        "total_burned": 6,
    },
    "Circular": {
        "id": 3,
        "total_count": 73,
        "total_burned": 4,
    },
    "Sparkle": {
        "id": 4,
        "total_count": 130,
        "total_burned": 21,
    },
    "Sleepy": {
        "id": 5,
        "total_count": 98555,
        "total_burned": 0,
    },
    "Dollop": {
        "id": 6,
        "total_count": 33076,
        "total_burned": 0,
    },
    "Twinkle": {
        "id": 7,
        "total_count": 55300,
        "total_burned": 0,
    },
    "Churro": {
        "id": 8,
        "total_count": 54205,
        "total_burned": 0,
    },
    "Sunny": {
        "id": 9,
        "total_count": 68608,
        "total_burned": 0,
    },
    "Hiccup": {
        "id": 10,
        "total_count": 1865,
        "total_burned": 0,
    },
    "Bullish": {
        "id": 11,
        "total_count": 8626,
        "total_burned": 0,
    },
    "Stormy Easter ‘21": {
        "id": 12,
        "total_count": 11105,
        "total_burned": 0,
    },
    "Flipsie Easter ‘21": {
        "id": 13,
        "total_count": 11350,
        "total_burned": 0,
    },
    "Cakeston Easter ‘21": {
        "id": 14,
        "total_count": 16857,
        "total_burned": 0,
    },
    "Easter '21 Champions": {
        "id": 15,
        "total_count": 499,
        "total_burned": 0,
    },
    "Syrup Soak": {
        "id": 16,
        "total_count": 13898,
        "total_burned": 0,
    },
    "Claire": {
        "id": 17,
        "total_count": 7288,
        "total_burned": 0,
    },
    "Lottie": {
        "id": 18,
        "total_count": 17466,
        "total_burned": 0,
    },
    "Lucky": {
        "id": 19,
        "total_count": 9320,
        "total_burned": 0,
    },
    "Baller": {
        "id": 20,
        "total_count": 42,
        "total_burned": 0,
    },
}


# In[76]:


def build_nft_report(sorted_orders):
    nfts = list()
    count = 0
    for order in sorted_orders:
        if "name" not in order or order["name"] is None:
            continue
        nft = dict()
        name = order["name"]
        token_id = order["token_id"]
        order_id = order["order_id"]
        symbol = order["symbol"]
        decimals = order["decimals"]
        price = order["price"]
        url_string = f"{ui_url}/{bunnies_collection_contract}/{token_id}/{order_id}"
        divisor = 10 ** int(decimals)
        unit_price = int(price) / divisor
        price_str = f"{unit_price} {symbol}{'':<10}"
        nft["total_price"] = unit_price
        if symbol == "BNB" or symbol == "WBNB":
            conv_usdx = unit_price * 502  # TODO: Fetch bnb price
            nft["total_price"] = conv_usdx
            price_str = f"{round(conv_usdx, 2)} {'USDx':<10} ({unit_price} {symbol}){'':<10}"
        nft["price_str"] = price_str
        nft["currency"] = symbol
        nft["name"] = name
        nft["url"] = url_string
        nfts.append(nft)
        count += 1
    nft_by_price = sorted(nfts, key=lambda i: (i['total_price'], i['currency']))
    print(f"--------------------------------------------------------------------------------------------------------")
    print(
        f"{sorted_orders[0]['name']:<25} total found {count} [{nft_by_price[0]['total_price']}, {nft_by_price[-1]['total_price']}]")
    print(f"--------------------------------------------------------------------------------------------------------")

    return nft_by_price


# In[64]:


def print_nft_report(nft_by_price):
    for nft in nft_by_price:
        print(f"{nft['name']:<25}{nft['price_str']:<20}{nft['url']}")


# In[24]:


def remove_dupes(dupe_list):
    return [dict(t) for t in {tuple(d.items()) for d in dupe_list}]


# In[26]:


def process_price_usdx(obj):
    price = obj["price"]
    decimals = obj["decimals"]
    symbol = obj["symbol"]
    divisor = 10 ** int(decimals)
    unit_price = int(price) / divisor
    price_str = f"{unit_price} {symbol}"
    conv_usdx = 0
    if symbol == "BNB" or symbol == "WBNB":
        conv_usdx = unit_price * 502  # TODO: Fetch bnb price
        price_str = f"{round(conv_usdx, 2)} USDx ({unit_price} {symbol})"
        unit_price = 0
    return (price_str, unit_price, conv_usdx)


# In[78]:


# bunny_ids = our_bunnies
for bunny in bunnies:
    try:
        response = requests.get(
            (
                f"{nft_api_url}{params}&page_size={limit}&contract="
                f"{bunnies_collection_contract}&sort_type=3&pros=bunnyId%3D{bunnies[bunny]['id']}"
            )
        )
        bunnies[bunny]["response"] = response
    except Exception as e:
        print(f"Request Error {e}")
    time.sleep(0.25)

# In[87]:


print(f"Results located on BSC and TreasureLand Market\n")
print(f"NFT Name{'':<15}NTFs Minted{'':<5}NFTs Burned{'':<5}In Orders (% of total suppy)")
print(f"--------------------------------------------------------------------------------------------------------")
total_nfts = 0
total_burned = 0
total_market = 0
for bunny in bunnies:
    try:
        data = bunnies[bunny]["response"].json()
    except Exception as e:
        print(f"Data Error {e}")
    orders = data["data"]["list"]
    if orders is not None and len(orders) > 0:
        count_on_market = data['data']['dataCount']
        bunny_count = bunnies[bunny]["total_count"]
        burn_count = bunnies[bunny]["total_burned"]
        pct_on_market = (count_on_market / (bunny_count - burn_count)) * 100
        message = f"{bunny_count:,}"
        if any(str(bunny) in s for s in ["Churro", "Sleepy", "Dollop", "Twinkle", "Sunny"]):
            message = f"{bunny_count:,}*"
        print((
            f"{bunny:<25}"
            f"{message:<15}"
            f"{burn_count:<10}\t"
            f"{count_on_market:<5,} ({round(pct_on_market, 2)}%)"
        ))
        sorted_orders = sorted(orders, key=lambda i: i['order_id'])
        total_nfts += bunny_count
        total_burned += burn_count
        total_market += count_on_market
        bunnies[bunny]["orders"] = sorted_orders
    else:
        print(f"Missing data for {bunny}")
print(f"--------------------------------------------------------------------------------------------------------")
print(f"{'':<10} TOTAL:{'':<8}{total_nfts:<15,}{total_burned:<15,}{total_market:,}")
print(f"\n\n")
print(f"*(not currently capped)")

# In[88]:


for bunny in bunnies:
    nfts = build_nft_report(bunnies[bunny]["orders"])
    print_nft_report(nfts)


# In[ ]:


# In[8]:


def query_trans(page_id):
    limit = 1000
    #     print(f"Received: {page_id}")
    response = requests.get(
        (
            f"{api_url}/latest/transaction?page={page_id}&chain_id=56&limit={limit}"
        )
    )
    return response


# In[11]:


transactions = dict()
page_start = 1
# print(f"Sent: {page_id}")
build_response = query_trans(page_start)
limit = 1000
try:
    response = build_response.json()
    # print(response)
except Exception as e:
    print(f"JSON error {e}")

total_transactions = response["data"]["total"]
total_pages = math.ceil(total_transactions / limit)
transactions["transactions"] = response["data"]["items"]

# print(transactions)
while page_start <= total_pages:
    page_start += 1
    #     print(f"Sent: {page_start}")
    full_rsp = query_trans(page_start)
    rsp = full_rsp.json()
    txns = rsp["data"]["items"]
    if txns is not None and len(txns) > 0:
        transactions["transactions"] = transactions["transactions"] + txns
    #     print((
    #         f"First TXN {transactions['transactions'][0]['name']}\n"
    #         f"Last TXN {transactions['transactions'][-1]['name']}"
    #     ))
    time.sleep(1)

# In[47]:


bunny_trades = list()
for transaction in transactions["transactions"]:
    if "contract" in transaction and transaction["contract"] == bunnies_collection_contract:
        if transaction["order_id"] == 214:
            # print(transaction)
            pass
        bunny_trades.append(transaction)

# print(bunny_trades)
print(len(bunny_trades))

# In[ ]:


# parsed = bunny_trades
# print(json.dumps(parsed, indent=4, sort_keys=True))


# In[50]:


# report = build_nft_report(bunny_trades)
sorted_bunny_trades = sorted(bunny_trades, key=lambda i: (i['name'], i['price']))
clean_list = remove_dupes(sorted_bunny_trades)
print(f"{len(clean_list)} Total Orders")
total_sales = 0
total_sold = 0
total_bought = dict()
total_count = dict()

for bunny in clean_list:
    name = bunny["name"]
    token_id = bunny["token_id"]
    order_id = bunny["order_id"]
    symbol = bunny["symbol"]
    decimals = bunny["decimals"]
    price = bunny["price"]
    url_string = f"{ui_url}/{bunnies_collection_contract}/{token_id}/{order_id}"
    total_volume, total_times_sold = format_sales(token_id)
    if total_volume == None or total_times_sold == None:
        print(f"{name} hasn't had a sales event {url_string}")
        continue
    total_sales += total_volume
    total_sold += total_times_sold
    if name in total_bought:
        # TODO: Convert me to list of numbers and sum up later so we can run stats
        total_count[name] += total_times_sold
        total_bought[name] += total_volume
    else:
        total_count[name] = total_times_sold
        total_bought[name] = total_volume
    print(f"{name:<25} {total_times_sold:<6,} {round(total_volume, 2):<10,} {url_string}")
    time.sleep(1)
# TODO: Time period as well, we only have block IDS


# In[89]:


print(f"Pancake Bunnies Sold On Market\n")
print(f"Name{'':<21}Quantity{'':<9}Volume (USDx){'':<9}Avg Price")
print(f"--------------------------------------------------------------------------------------------------------")
for bunny in bunnies:
    avg_price = total_bought[bunny] / total_count[bunny]
    try:
        print((
            f"{bunny:<25} {round(total_count[bunny], 2):<15,} {round(total_bought[bunny], 2):<20,} {round(avg_price, 2):,}"
        ))
    except Exception as e:
        # print(f"Error {e}")
        pass
print(f"--------------------------------------------------------------------------------------------------------")
print(f"Totals{'':<20}{total_sold:<12,}{round(total_sales, 2):<3,} USDx")


# In[48]:


def get_token_history(token_id):
    try:
        response = requests.get(f"{api_url}/nft/history?chain_id=56&contract={bunnies_collection_contract}&token_id={token_id}")
        response = response.json()
        return response
    except Exception as e:
        print(f"Error: {e}")
    return None


# In[49]:


def format_sales(token_id):
    sales = list()
    total_volume = 0
    total_times_sold = 0

    history = get_token_history(token_id)

    if history is None:
        return None, None

    if "data" not in history:
        return None, None

    if len(history["data"]) <= 0:
        return None, None

    for event in history["data"]:
        if event["type"] == "Sale":
            sales.append(event)

    sales = remove_dupes(sales)

    for sale in sales:
        price_str, unit_price, conv_usdx = process_price_usdx(sale)
        total_times_sold += 1
        total_volume += (conv_usdx + unit_price)

    return (total_volume, total_times_sold)

# In[23]:


# In[ ]:


# In[ ]:


# In[ ]:


# In[ ]:


# In[ ]:


# summary = requests.get((
#     f"https://api.treasureland.market/v2/v1/nft/collect/"
#     f"rank?chain_id=56&sort=-2&key_word=&payment_token=0x0000000000000000000000000000000000000000"
# ))
# struct_summary = summary.json()
# print(struct_summary["data"])
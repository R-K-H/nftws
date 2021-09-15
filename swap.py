#!/usr/bin/env python
# coding: utf-8
import math
import time

import numpy as np
import requests
import ujson
from bsc.smart_contracts.pancake_bunny import *
from bsc.tokens.bep_721 import *
from web3 import Web3
from web3.middleware import geth_poa_middleware

POOL_INDEX = 0
PANCAKE_BUNNY = pancake_bunny_hashed_address

w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed1.ninicoin.io/56'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
# w3.isConnected()

bunny_ABI = pancake_bunny_ABI
bunnies_contract = w3.eth.contract(address=PANCAKE_BUNNY, abi=bunny_ABI)

ui_url = "https://www.treasureland.market/assets"
api_url = "https://api.treasureland.market/v2/v1"
base_url = "https://api.treasureland.market/v2/v1/nft/"
chain_id = 56
limit = 1000

contract ="0xdf7952b35f24acf7fc0487d01c8d5690a60dba07"
# Total NFTs: 408549
bunnies = nfts["pancake-bunnies"]


def build_nft_report(sorted_orders):
    nfts = list()
    count = 0
    prices = list()
    sorted_orders = remove_dupes(sorted_orders)
    
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
        url_string = f"{ui_url}/{contract}/{token_id}/{order_id}"
        price_str, unit_price, conv_usdx = process_price_usdx(order)
        total_price = unit_price + conv_usdx
        nft["total_price"] = total_price
        nft["price_str"] = price_str
        nft["currency"] = symbol
        nft["name"] = name
        nft["url"] = url_string
        nfts.append(nft)
        prices.append(total_price)
        count +=1
    nft_by_price = sorted(nfts, key = lambda i: (i['total_price'],i['currency']))
    print((
        f"{nft_by_price[0]['name']:<25}"
        f"{len(nft_by_price):<6,}"
        f"{round(nft_by_price[0]['total_price'], 2):<20,}"
        f"{round(nft_by_price[-1]['total_price'], 2):<20,}"
        f"{round(np.average(prices),2):<20,}"
        f"{round(np.quantile(prices, 0.25),2):<20,}"
        f"{round(np.quantile(prices, 0.5),2):<20,}"
        f"{round(np.quantile(prices, 0.75),2):<20,}"
    ))
    print(f"-----------------------------------------------------------------------------------------------------------------------------------------------------------------------")

    return nft_by_price


def query_trans(page_id):
    limit = 1000
#     print(f"Received: {page_id}")
    response = requests.get(
        (
            f"{api_url}/latest/transaction?page={page_id}&chain_id=56&limit={limit}"
        )
    )
    return response


def print_nft_report(nft_by_price):
    for nft in nft_by_price:
        print(f"{nft['name']:<25}{nft['price_str']:<20} {nft['url']}")


def remove_dupes(dupe_list):
    return [dict(t) for t in {tuple(d.items()) for d in dupe_list}]


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
        price_str = f"{round(conv_usdx,2)} USDx ({unit_price} {symbol})"
        unit_price = 0
    return (price_str, unit_price, conv_usdx)


def get_token_history(token_id):
    try:
        response = requests.get(f"{api_url}/nft/history?chain_id=56&contract={contract}&token_id={token_id}")
        response = response.json()
        return response
    except Exception as e:
        print(f"Error: {e}")
    return None


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


def query_open_orders(page_number):
    params = "items?chain_id=56&page_no=1"
    try:
        response = requests.get(
            (
                f"{base_url}items?chain_id=56&"
                f"page={page_number}&"
                f"page_size={limit}&"
                # f"sort_type=2&"
                f"contract={contract}"
            )
        )
        return response
    except Exception as e:
        print(f"Request Error {e}")
        return None


def get_orders():
    items = list()
    try:
        page_count = 1
        response = query_open_orders(page_count)
        if response is None:
            print("Error")
            return None
        data = response.json()
        # print(data)
        items = data["data"]["list"]
        item_count = data["data"]["dataCount"]
        print(f"Total Count: {item_count}")
        items_received = int(limit)
        if int(item_count) > int(limit):
            while items_received < int(item_count):
                print("Recursion")
                page_count += 1
                items_received = int(page_count) * int(limit)
                response = query_open_orders(page_count)
                if response is None:
                    print("Error")
                    return None
                data = response.json()
                items = items + data["data"]["list"]
    except Exception as e:
        print(f"Error with JSON {e}")
    if items is None or len(items) < 1:
        return
    for item in items:
        # print(item)
        if "name" not in item:
            print(f"Name not found")
            continue
        if item["name"] is None:
            print(f"Error with name is None")
            continue

        if "items" not in bunnies[item["name"]]:
            bunnies[item["name"]]["items"] = list()

        bunnies[item["name"]]["items"].append(item)
    return (bunnies, item_count)


def get_market_transactions():
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

    bunny_trades = list()
    for transaction in transactions["transactions"]:
        if "contract" in transaction and transaction["contract"] == contract:
            if transaction["order_id"] == 214:
                # print(transaction)
                pass
            bunny_trades.append(transaction)

    # print(bunny_trades)
    print(len(bunny_trades))
    sorted_bunny_trades = sorted(bunny_trades, key = lambda i: (i['name'], i['price']))
    clean_list = remove_dupes(sorted_bunny_trades)
    print(f"{len(clean_list)} Total Orders")
    total_sales = 0
    total_sold = 0
    total_bought = dict()
    total_count = dict()
    prices = dict()
    for bunny in clean_list:
        # TODO: Setup dict of list for analysis for ACTUAL ORDERS
        # prices[bunny] = price
        name = bunny["name"]
        token_id = bunny["token_id"]
        order_id = bunny["order_id"]
        symbol = bunny["symbol"]
        decimals = bunny["decimals"]
        price = bunny["price"]
        url_string = f"{ui_url}/{contract}/{token_id}/{order_id}"
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
        print(f"{name:<25} {total_times_sold:<6,} {round(total_volume,2):<10,} {url_string}")
        time.sleep(1)
    
    print(f"Pancake Bunnies Sold On Market\n")
    print(f"Name{'':<21}Quantity{'':<9}Volume (USDx){'':<9}Avg Price")
    print(f"--------------------------------------------------------------------------------------------------------")
    for bunny in bunnies:
        avg_price = total_bought[bunny] / total_count[bunny]
        try:
            print((
                f"{bunny:<25} {round(total_count[bunny],2):<15,} {round(total_bought[bunny],2):<20,} {round(avg_price,2):,}"
            ))
        except Exception as e:
            # print(f"Error {e}")
            pass
    print(f"--------------------------------------------------------------------------------------------------------")
    print(f"Totals{'':<20}{total_sold:<12,}{round(total_sales,2):<3,} USDx")


for bunny in bunnies: 
    bunny_burn = bunnies_contract.functions.bunnyBurnCount(bunnies[bunny]["id"]).call()
    bunny_count = bunnies_contract.functions.bunnyCount(bunnies[bunny]["id"]).call()
    bunnies[bunny]["total_burned"] = bunny_burn
    bunnies[bunny]["total_count"] = bunny_count

bunnnies, item_count = get_orders()

print(f"Results located on BSC and TreasureLand Market\n")
print(f"NFT Name{'':<15}NTFs Minted{'':<5}NFTs Burned{'':<5}In Orders (% of total suppy)")
print(f"--------------------------------------------------------------------------------------------------------")
total_nfts = 0
total_burned = 0
total_market = 0
error = list()
for bunny in bunnies:
    orders = bunnies[bunny]['items']
    # print(f"Total count: {len(orders)}")
    if orders is not None and len(orders) > 0:
        orders = remove_dupes(orders)
        # print(f"Removed Dupes: {len(orders)}")
        count_on_market = len(orders)
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
            f"{count_on_market:<5,}"
            f"({round(pct_on_market, 2)}%)"
        ))
        sorted_orders = sorted(orders, key = lambda i: i['order_id'])
        total_nfts += bunny_count
        total_burned += burn_count
        total_market += count_on_market
        bunnies[bunny]["orders"] = sorted_orders
    else:
        print(f"Missing data for {bunny}")
    # print(count_on_market)
print(f"--------------------------------------------------------------------------------------------------------")
print(f"{'':<10} TOTAL:{'':<8}{total_nfts:<15,}{total_burned:<15,}{total_market:,}")
print(f"\n\n")
print(f"*(not currently capped)")
if error is not None and len(error) > 0:
    print(f"{error}")

print(f"Prices in USDx; Quantity on Secondary Market TreasureLand\n")
print(f"{'Name':<25}{'Qty':<6}{'Min Price':<20}{'Max Price':<20}{'Average Price':<20}{'25%':<20}{'50%':<20}75%")
print(f"-----------------------------------------------------------------------------------------------------------------------------------------------------------------------")
for bunny in bunnies:
    #print(bunnies[bunny]["response"])
    nfts = build_nft_report(bunnies[bunny]["orders"])
    # print_nft_report(nfts)

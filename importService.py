import asyncio
import time

import aiohttp
import asyncpg
from asyncpg import UniqueViolationError

from bsc.abis.pancake_bunny_contract import *
from bsc.tokens.bep_20 import *
from bsc.tokens.bep_721 import *


async def setup_transaction_db():
    conn = await asyncpg.connect(
        host="localhost",
        database="nfts",
        user="root",
        password="toor")

    try:
        await conn.execute('''
            CREATE TABLE transactions (
        order_id int NOT null primary key,
        chain_id int not null,
        contract varchar(255) not null,
        token_id varchar(100) not null,
        name varchar(255) not null,
        resource varchar(255) not null,
        resource_type varchar(100) not null,
        maker varchar(255) not null,
        taker varchar(255) not null,
        side int not null,
        price float not null,
        erc20 varchar(255) not null,
        status int not null,
        title varchar(255) not null,
        symbol varchar(100) not null,
        decimals int not null,
        show_decimals int not null
    );''')
        print('table transactions created')
    except:
        print("table transactions already created")
    try:
        await conn.execute('''
            CREATE TABLE items (
        token_id varchar(100) NOT null primary key,
        chain_id int not null,
        contract varchar(255) not null,
        name varchar(255) not null,
        resource varchar(255) not null,
        resource_type varchar(100) not null,
        token_uri varchar(255) not null,
        price float not null,
        order_id int not null,
        collect_name varchar(255) not null,
        erc_type varchar(255) not null,
        side int not null,
        maker varchar(255) not null,
        taker varchar(255) not null,
        thumb varchar(255) not null,
        decimals int not null,
        show_decimals int not null,
        creator_status int not null
    );''')
        print('table items created')
    except:
        print("table items already created")
    return conn


class ImportService:
    def __init__(self):
        self.is_done = False  # Use an array of those to do multiple imports at the same time
        self.is_limit_reached = False

        self.bunnies = nfts["pancake-bunnies"]
        self.bunny_names = self.bunnies.keys()
        self.tokens = tokens
        self.pancake_bunny_hashed_address = pancake_bunny_hashed_address
        self.pancake_bunny_ABI = pancake_bunny_ABI

    async def import_transactions(self):
        # If the orderIds are chronological: get the max one from db and fetch them chronologically sorted.
        # Stop at the max from db so we download them incrementally.
        conn = await setup_transaction_db()
        loop = asyncio.get_event_loop()
        self.is_done = False

        async with aiohttp.ClientSession() as session:
            current_page = 0
            while not self.is_done:
                if self.is_limit_reached:
                    time.sleep(30)  # Everything gets delayed by 30 seconds
                    self.is_limit_reached = False
                current_page += 1
                transactions_url = f'https://api.treasureland.market/v2/v1/latest/transaction?page={current_page}&chain_id=56&limit=1000'
                time.sleep(1)  # Rate limit 60 calls per minute

                # Doesn't work, why?
                # To kill the program : ps -aef | grep "python3 main.py"$ | awk '{print $2}' | xargs sudo kill -9
                # print('Creating tasks with url:' + str(transactions_url))
                # loop.create_task(self.fetch_and_save_transactions(conn, session, transactions_url))

                # Works but slooowwwww
                await self.fetch_and_save_transactions(conn, session, transactions_url)

    async def fetch_and_save_transactions(self, conn, session, transactions_url):
        print('querying:' + str(transactions_url))
        async with session.get(transactions_url) as resp:
            if resp.status == 429:  # Rate limit reached, let's avoid being blacklisted
                print('429 received, sleeping for 30 seconds to avoid blacklisting')
                self.is_limit_reached = True
                time.sleep(30)

            if resp.status == 200:  # All good
                json_resp = await resp.json()

                if json_resp['data']['items'] is None:  # We're done
                    self.is_done = True
                    print("We're done")
                    return

                transactions = json_resp['data']['items']
                for transaction in transactions:
                    if transaction['symbol'] == 'BNB' and transaction['name'] in self.bunny_names:
                        try:
                            await conn.execute('''
                                    INSERT INTO public.transactions
        (token_id, order_id, chain_id, contract, "name", resource, resource_type, maker, taker, side, price, erc20, status, title, symbol, decimals, show_decimals)
        VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                                ''',
                                               transaction['token_id'],
                                               transaction['order_id'],
                                               transaction['chain_id'],
                                               transaction['contract'],
                                               transaction['name'],
                                               transaction['resource'],
                                               transaction['resource_type'],
                                               transaction['maker'],
                                               transaction['taker'],
                                               transaction['side'],
                                               float(transaction['price']) / 1000000000000000000,
                                               transaction['erc20'],
                                               transaction['status'],
                                               transaction['title'],
                                               transaction['symbol'],
                                               transaction['decimals'],
                                               transaction['show_decimals'])
                        except UniqueViolationError:
                            print("Transaction with orderid:" + str(transaction['order_id']) + " is already in db")
                print("1000 transactions saved")

    async def import_items(self):
        # If the orderIds are chronological: get the max one from db and fetch them chronologically sorted.
        # Stop at the max from db so we download them incrementally.
        conn = await setup_transaction_db()
        loop = asyncio.get_event_loop()
        self.is_done = False

        async with aiohttp.ClientSession() as session:
            current_page = 0
            while not self.is_done:
                if self.is_limit_reached:
                    time.sleep(30)  # Everything gets delayed by 30 seconds
                    self.is_limit_reached = False
                current_page += 1
                items_url = f'https://api.treasureland.market/v2/v1/nft/items?chain_id=56&page_no={current_page}&page_size=100&contract=0xdf7952b35f24acf7fc0487d01c8d5690a60dba07&sort_type=1&pros='
                time.sleep(1)  # Rate limit 60 calls per minute

                await self.fetch_and_save_items(conn, session, items_url)

    async def fetch_and_save_items(self, conn, session, items_url):
        print('querying:' + str(items_url))
        async with session.get(items_url) as resp:
            if resp.status == 429:  # Rate limit reached, let's avoid being blacklisted
                print('429 received, sleeping for 30 seconds to avoid blacklisting')
                self.is_limit_reached = True
                time.sleep(30)

            if resp.status == 200:  # All good
                json_resp = await resp.json()

                if json_resp['data']['list'] is None:  # We're done
                    self.is_done = True
                    print("We're done")
                    return

                items = json_resp['data']['list']
                for item in items:
                    try:
                        await conn.execute('''
                                   INSERT INTO public.items
       (token_id, chain_id, contract, "name", resource, resource_type, token_uri, price, order_id, collect_name, erc_type, side, maker, taker, thumb, decimals, show_decimals, creator_status)
       VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                               ''',
                                           item['token_id'],
                                           item['chain_id'],
                                           item['contract'],
                                           item['name'],
                                           item['resource'],
                                           item['resource_type'],
                                           item['token_uri'],
                                           float(item['price']) / 1000000000000000000,
                                           item['order_id'],
                                           item['collect_name'],
                                           item['erc_type'],
                                           item['side'],
                                           item['maker'],
                                           item['taker'],
                                           item['thumb'],
                                           item['decimals'],
                                           item['show_decimals'],
                                           item['creator_status'])
                    except UniqueViolationError:
                        print("Item with token_id:" + str(item['token_id']) + " is already in db")
                print("100 items saved")

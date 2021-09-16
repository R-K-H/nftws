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
        price varchar(255) not null,
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

    return conn


class ImportService:
    def __init__(self):
        self.is_done = False  # Use an array of those to do multiple imports at the same time
        self.is_limit_reached = False

        self.bunnies = nfts["pancake-bunnies"]
        self.tokens = tokens
        self.pancake_bunny_hashed_address = pancake_bunny_hashed_address
        self.pancake_bunny_ABI = pancake_bunny_ABI

    async def import_transactions(self):
        # If the orderIds are chronological: get the max one from db and fetch them chronologically sorted.
        # Stop at the max from db so we download them incrementally.
        conn = await setup_transaction_db()
        loop = asyncio.get_event_loop()

        async with aiohttp.ClientSession() as session:
            current_page = 0
            while not self.is_done:
                if self.is_limit_reached:
                    time.sleep(30)  # Everything gets delayed by 30 seconds
                    self.is_limit_reached = False
                current_page += 1
                transactions_url = f'https://api.treasureland.market/v2/v1/latest/transaction?page={current_page}&chain_id=56&limit=10'
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

                transactions = json_resp['data']['items']
                for transaction in transactions:
                    try:
                        await conn.execute('''
                                INSERT INTO public.transactions
    (order_id, chain_id, contract, token_id, "name", resource, resource_type, maker, taker, side, price, erc20, status, title, symbol, decimals, show_decimals)
    VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                            ''',
                                           transaction['order_id'],
                                           transaction['chain_id'],
                                           transaction['contract'],
                                           transaction['token_id'],
                                           transaction['name'],
                                           transaction['resource'],
                                           transaction['resource_type'],
                                           transaction['maker'],
                                           transaction['taker'],
                                           transaction['side'],
                                           transaction['price'],
                                           transaction['erc20'],
                                           transaction['status'],
                                           transaction['title'],
                                           transaction['symbol'],
                                           transaction['decimals'],
                                           transaction['show_decimals'])
                    except UniqueViolationError:
                        print("Transaction with orderid:" + str(transaction['order_id']) + " is already in db")

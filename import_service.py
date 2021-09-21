import asyncio
import time
from asyncio import AbstractEventLoop

import aiohttp
import asyncpg
import sanic
from asyncpg import UniqueViolationError
from bsc.abis.pancake_bunny_contract import *
from bsc.tokens.bep_20 import *
from bsc.tokens.bep_721 import *
from config.constants import (BSC_CHAIN_ID, BUNNY_CONTRACT, TLM_API_URL,
                              TLM_API_VERSION)
from sanic.log import logger


class ImportService:
    def __init__(self, database, loop: AbstractEventLoop):
        self.is_done = False  # Use an array of those to do multiple imports at the same time
        self.is_limit_reached = False

        self.bunnies = nfts["pancake-bunnies"]
        self.bunny_names = self.bunnies.keys()
        self.tokens = tokens
        self.loop = loop
        self.database = database
        self.pancake_bunny_hashed_address = pancake_bunny_hashed_address
        self.pancake_bunny_ABI = pancake_bunny_ABI
        self.page_size = 100

    def initalize(self):
        setup_db = False
        if setup_db:
            self.databse.initalize()
        else:
            print("already setup")

    async def import_transactions(self) -> None:
        # If the orderIds are chronological: get the max one from db and fetch them chronologically sorted.
        # Stop at the max from db so we download them incrementally.
        # conn = await setup_transaction_db()
        # TODO: setup initialized somewhere?
        # loop = asyncio.get_event_loop()
        self.is_done = False
        logger.info("Importing Transactions")
        async with aiohttp.ClientSession() as session:
            current_page = 0
            while not self.is_done:
                if self.is_limit_reached:
                    logger.info("Request limit reached, taking a 30s break")
                    time.sleep(30)  # Everything gets delayed by 30 seconds
                    self.is_limit_reached = False
                current_page += 1
                api_endpoint = f"{TLM_API_URL}/{TLM_API_VERSION}latest/transaction?"
                params = (
                    f"chain_id={BSC_CHAIN_ID}&"
                    f"page={current_page}&"
                    f"limit={self.page_size * 10}"
                )
                transactions_url = api_endpoint + params
                time.sleep(1)  # Rate limit 60 calls per minute

                # Doesn't work, why?
                # To kill the program : ps -aef | grep "python3 main.py"$ | awk '{print $2}' | xargs sudo kill -9
                # print('Creating tasks with url:' + str(transactions_url))
                # self.loop.create_task(self.fetch_and_save_transactions(session, transactions_url))

                # Works but slooowwwww
                await self.fetch_and_save_transactions(session, transactions_url)
                break

    async def fetch_and_save_transactions(self, session, transactions_url):
        logger.info(f"Querying: {str(transactions_url)}")
        async with session.get(transactions_url) as resp:
            if resp.status == 429:  # Rate limit reached, let's avoid being blacklisted
                logger.info(f"429 received, sleeping for 30 seconds to avoid blacklisting")
                self.is_limit_reached = True
                time.sleep(30)

            if resp.status == 200:  # All good
                json_resp = await resp.json()

                if json_resp['data']['items'] is None:  # We're done
                    self.is_done = True
                    logger.info("We're done")
                    return

                transactions = json_resp['data']['items']
                for transaction in transactions:
                    if transaction['symbol'] == 'BNB' and transaction['name'] in self.bunny_names:
                        self.loop.create_task(self.database.insert_transaction(transaction))
                logger.info("1000 transactions saved")

    async def import_items(self):
        # If the orderIds are chronological: get the max one from db and fetch them chronologically sorted.
        # Stop at the max from db so we download them incrementally.
        # conn = await setup_transaction_db()
        self.is_done = False

        async with aiohttp.ClientSession() as session:
            current_page = 0
            while not self.is_done:
                if self.is_limit_reached:
                    logger.info("Request limit reached, taking a 30s break")
                    time.sleep(30)  # Everything gets delayed by 30 seconds
                    self.is_limit_reached = False
                current_page += 1
                api_endpoint = f"{TLM_API_URL}/{TLM_API_VERSION}/nft/items?"
                params = (
                    f"chain_id={BSC_CHAIN_ID}&"
                    f"page_no={current_page}&"
                    f"page_size={self.page_size}&"
                    f"contract={BUNNY_CONTRACT}"
                )
                items_url = api_endpoint + params
                time.sleep(1)  # Rate limit 60 calls per minute

                await self.fetch_and_save_items(session, items_url)

    async def fetch_and_save_items(self, session, items_url):
        print('querying:' + str(items_url))
        async with session.get(items_url) as resp:
            if resp.status == 429:  # Rate limit reached, let's avoid being blacklisted
                logger.info("429 received, sleeping for 30 seconds to avoid blacklisting")
                self.is_limit_reached = True
                time.sleep(30)

            if resp.status == 200:  # All good
                json_resp = await resp.json()

                if json_resp['data']['list'] is None:  # We're done
                    self.is_done = True
                    logger.info("We're done")
                    return

                items = json_resp['data']['list']
                for item in items:
                    self.loop.create_task(self.database.insert_item(item))
                logger.info("100 items saved")

import asyncio
import time
from asyncio import AbstractEventLoop

import aiohttp
import asyncpg
from asyncpg import Pool, Record, UniqueViolationError
from bsc.abis.pancake_bunny_contract import *
from bsc.tokens.bep_20 import *
from bsc.tokens.bep_721 import *


class Database:
    def __init__(self, db_config: dict, loop: AbstractEventLoop) -> None:
        self.db_config = db_config
        self.loop = loop
        self.pool: Pool
        self.connected: bool = False

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(**self.db_config,)
        self.connected = True

    async def initalize(self) -> None:
        self.setup_transactions_table()
        self.setup_items_table()

    async def setup_transactions_table(self) -> None:
        try:
            async with self.pool.acquire() as conn:
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
        except Exception as e:
            print(f"table transactions already created: {e}")

    async def setup_items_table(self) -> None:
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    '''
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
                    )
                    '''
                )
                print('table items created')
        except Exception as e:
            print(f"table items already created {e}")

    async def insert_item(self, item: dict) -> None:
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    '''
                        INSERT INTO public.items
                        (
                            token_id,
                            chain_id,
                            contract,
                            "name",
                            resource,
                            resource_type,
                            token_uri,
                            price,
                            order_id,
                            collect_name,
                            erc_type,
                            side,
                            maker,
                            taker,
                            thumb,
                            decimals,
                            show_decimals,
                            creator_status
                        )
                        VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
                        )
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
        except UniqueViolationError as e:
            print("Item with token_id:" + str(item['token_id']) + " is already in db")
        except Exception as e:
            print(f"Error: {e}")

    async def insert_transaction(self, transaction: dict) -> None:
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    '''
                        INSERT INTO public.transactions
                        (
                            token_id,
                            order_id,
                            chain_id,
                            contract,
                            "name",
                            resource,
                            resource_type,
                            maker,
                            taker,
                            side,
                            price,
                            erc20,
                            status,
                            title,
                            symbol,
                            decimals,
                            show_decimals
                        )
                        VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17
                        )
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
                    float(transaction['price']) / 1000000000000000000,  # TODO: Review me
                    transaction['erc20'],
                    transaction['status'],
                    transaction['title'],
                    transaction['symbol'],
                    transaction['decimals'],
                    transaction['show_decimals']
                )
        except UniqueViolationError as e:
            print("Transaction with orderid:" + str(transaction['order_id']) + " is already in db")
        except Exception as e:
            print(f"Error: {e}")

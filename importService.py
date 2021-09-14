from bsc.abis.pancake_bunny import *
from bsc.tokens.bep_20 import *
from bsc.tokens.bep_721 import *


class ImportService:
    def __init__(self, conn):
        self.cur = conn.cursor()
        print("Import service instantiated")
        self.bunnies = nfts["pancake-bunnies"]
        self.tokens = tokens
        self.pancake_bunny_hashed_address = pancake_bunny_hashed_address
        self.pancake_bunny_ABI = pancake_bunny_ABI

    async def import_bunnies(self):
        print("Hello!")

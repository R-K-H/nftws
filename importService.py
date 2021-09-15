from bsc.abis.pancake_bunny_contract import *
from bsc.tokens.bep_20 import *
from bsc.tokens.bep_721 import *


class ImportService:
    def __init__(self, conn):
        self.bunnies = nfts["pancake-bunnies"]
        self.tokens = tokens
        self.pancake_bunny_hashed_address = pancake_bunny_hashed_address
        self.pancake_bunny_ABI = pancake_bunny_ABI
        print("Import service instantiated")

    async def import_bunnies(self):
        print("Hello!")

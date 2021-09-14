import bunnies

class ImportService:
    def __init__(self, conn):
        self.cur = conn.cursor()
        print("Import service instantiated")
        self.bunnies = bunnies.bunnies

    async def import_bunnies(self):
        print("Hello!")

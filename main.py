import asyncio

from sanic import Sanic, response

import importService

# Consider https://github.com/MagicStack/asyncpg in place of psycopg2

app = Sanic("NFTWS")

importService = importService.ImportService()


@app.route('/')
async def hello(request):
    return response.text("Service up!")


@app.route('/import')
async def import_bunnies(request):
    # Check if db is empty, if not cancel to avoid human errors. Create emptyDb endpoint as well. Later will be incremental
    loop = asyncio.get_event_loop()
    loop.create_task(importService.import_transactions())
    return response.text('Import of transactions started')


if __name__ == '__main__':
    app.run()

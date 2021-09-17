import asyncio

from sanic import Sanic, response

import importService


app = Sanic("NFTWS")

importService = importService.ImportService()


@app.route('/')
async def hello(request):
    return response.text("Service up!")


@app.route('/import')
async def import_bunnies(request):
    loop = asyncio.get_event_loop()
    loop.create_task(importService.import_transactions())
    return response.text('Import of transactions started')


@app.route('/items')
async def import_items(request):
    loop = asyncio.get_event_loop()
    loop.create_task(importService.import_items())
    return response.text('Import of items started')


if __name__ == '__main__':
    app.run()

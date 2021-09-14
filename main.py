import psycopg2
from sanic import Sanic, response
import asyncio
import importService


app = Sanic("NFTWS")

conn = psycopg2.connect(
    host="localhost",
    database="nfts",
    user="root",
    password="toor")

importService = importService.ImportService(conn)


@app.route('/')
async def hello(request):
    return response.text("Service up!")


@app.route('/import')
async def import_bunnies(request):
    # Check if db is empty, if not cancel to avoid human errors. Create emptyDb endpoint as well.
    loop = asyncio.get_event_loop()
    loop.create_task(importService.import_bunnies())
    return response.text('Import of bunnies started')


if __name__ == '__main__':
    app.run()

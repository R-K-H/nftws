"""NFTWS API."""

import asyncio
from asyncio import AbstractEventLoop

from database import Database
from import_service import ImportService
from sanic import HTTPResponse, Request, Sanic, exceptions
from sanic.exceptions import (Forbidden, InvalidUsage, NotFound,
                              SanicException, ServerError, Unauthorized)
from sanic.log import logger
from sanic.response import html, json, text

app = Sanic("NFTWS")
app.config.DEBUG = True

db_config = {
    "host": "localhost",
    "database": "nfts",
    "user": "root",
    "password": "toor"
}


@app.route("/ping", methods=["GET"])
async def ping(request: Request) -> HTTPResponse:
    logger.info(f"{request}")
    return text("Pong!")


@app.route("/import", methods=["GET"])
async def import_bunnies(request: Request) -> HTTPResponse:
    await app.ctx.import_service.import_transactions()
    return text('Import of transactions started')


@app.route('/items', methods=["GET"])
async def import_items(request: Request) -> HTTPResponse:
    await app.ctx.import_service.import_items()
    return text('Import of items started')


@app.route("/collection", methods=["GET"])
async def get_collection(request: Request) -> HTTPResponse:
    return json({"message": "Not implemented yet"})


@app.before_server_start
async def setup_database(app: Sanic, loop: AbstractEventLoop) -> None:
    app.ctx.db = Database(app.config.DB_CONFIG, loop=loop)
    # await app.ctx.db.connect()
    app.ctx.import_service = ImportService(app.ctx.db, loop=loop)

if __name__ == '__main__':
    app.config.DB_CONFIG = db_config
    app.run()

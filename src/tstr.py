#!/usr/bin/env python3
# tstr - web-based testing framework
# Copyright (C) 2022 SUSE LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

from fastapi import FastAPI
from fastapi.logger import logger
import uvicorn  # type: ignore

from libtstr.api import heads

from libtstr.misc import setup_logging


setup_logging("DEBUG")


api_tags = [
    {
        "name": "workqueue",
        "description": "Work Queue related operations.",
    },
    {
        "name": "heads",
        "description": "Branches and PR related operations.",
    },
]

app = FastAPI(docs_url=None)
api = FastAPI(
    title="tstr",
    description="Web-based testing framework.",
    version="0.0.1",
    openapi_tags=api_tags,
)


@app.on_event("startup")  # type: ignore
async def on_startup():
    logger.info("starting tstr server")


@app.on_event("shutdown")  # type: ignore
async def on_shutdown():
    logger.info("shutting down tstr server.")


api.include_router(heads.router)
app.mount("/api", api, name="API")

# uvicorn.run(app, host="0.0.0.0", port=31337)  # type: ignore

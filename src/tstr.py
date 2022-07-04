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

# pyright: reportMissingTypeArgument=false

import asyncio
import os
from pathlib import Path
import sys
from typing import Optional
from fastapi import FastAPI
from fastapi.logger import logger
import uvicorn  # type: ignore
from libtstr.gh import GithubMgr

from libtstr.misc import setup_logging
from libtstr.db import database
from libtstr.state import TstrState
from libtstr.config import TstrConfig

# routers
#
from libtstr.api import heads


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


api.include_router(heads.router)
app.mount("/api", api, name="API")


_shutting_down: bool = False
_main_task: Optional[asyncio.Task] = None


async def tstr_main_task(app: FastAPI, state: TstrState) -> None:

    state.github = GithubMgr(state.config.gh)

    while not _shutting_down:
        logger.debug("tstr main task")
        await asyncio.sleep(1.0)

    logger.info("shutting down main tstr task.")


@app.on_event("startup")  # type: ignore
async def on_startup():
    cfgpath = Path(os.getenv("TSTR_CONFIG", "tstr.cfg"))
    if not cfgpath.exists() or not cfgpath.is_file():
        print("missing configuration file.")
        sys.exit(1)

    try:
        config = TstrConfig.parse_file(cfgpath)
    except:
        print("unable to parse config file")
        sys.exit(1)

    setup_logging(config.log_level)
    logger.info("starting tstr server")
    logger.debug(f"config: {config}")

    state = TstrState()
    state.config = config
    state.database = database
    api.state.tstr = state

    if not state.database.is_connected:
        await state.database.connect()

    global _main_task
    _main_task = asyncio.create_task(tstr_main_task(app, state))


@app.on_event("shutdown")  # type: ignore
async def on_shutdown():
    logger.info("shutting down tstr server.")

    global _shutting_down
    _shutting_down = True
    if _main_task is not None:
        await _main_task

    state: TstrState = api.state.tstr
    if state.database.is_connected:
        await state.database.disconnect()


# uvicorn.run(app, host="0.0.0.0", port=31337)  # type: ignore

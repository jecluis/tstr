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
from fastapi import FastAPI, Request, status
from fastapi.logger import logger
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uvicorn  # type: ignore

from libtstr.misc import setup_logging
from libtstr.db import database
from libtstr.state import TstrState
from libtstr.config import TstrConfig
from libtstr.wq import WorkQueue
from libtstr.gh import GithubMgr

# routers
#
from libtstr.api import heads
from libtstr.api import wq
from libtstr.api import bench


api_tags = [
    {
        "name": "workqueue",
        "description": "Work Queue related operations.",
    },
    {
        "name": "heads",
        "description": "Branches and PR related operations.",
    },
    {"name": "benchmark", "description": "Benchmark results."},
]

app = FastAPI(docs_url=None)
api = FastAPI(
    title="tstr",
    description="Web-based testing framework.",
    version="0.0.1",
    openapi_tags=api_tags,
)


api.include_router(heads.router)
api.include_router(wq.router)
api.include_router(bench.router)
app.mount("/api", api, name="API")

app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")


_shutting_down: bool = False
_main_task: Optional[asyncio.Task] = None


async def tstr_main_task(app: FastAPI, state: TstrState) -> None:

    state.github = GithubMgr(state.config.gh)
    state.workqueue = WorkQueue()
    await state.github.start()
    state.workqueue.start()

    while not _shutting_down:
        logger.debug("tstr main task")
        await asyncio.sleep(1.0)

    logger.info("shutting down main tstr task.")
    await state.workqueue.stop()
    await state.github.stop()


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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    exc_str = f"{exc}".replace("\n", " ").replace("  ", " ")
    logger.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


# uvicorn.run(app, host="0.0.0.0", port=31337)  # type: ignore

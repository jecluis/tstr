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

import logging.config
from fastapi import FastAPI
from fastapi.logger import logger
import uvicorn  # type: ignore

from libtstr.api import heads


def setup_logging(lvl: str) -> None:
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": (
                    "[%(levelname)-5s] %(asctime)s -- "
                    "%(module)s -- %(message)s"
                ),
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
            "colorized": {
                "()": "uvicorn.logging.ColourizedFormatter",
                "format": (
                    "%(levelprefix)s %(asctime)s -- "
                    "%(module)s -- %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "level": lvl,
                "class": "logging.StreamHandler",
                "formatter": "colorized",
            },
            "log_file": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "simple",
                "filename": "tstr.log",
                "maxBytes": 10485760,
                "backupCount": 1,
            },
        },
        "loggers": {
            "uvicorn": {
                "level": "DEBUG",
                "handlers": ["console", "log_file"],
                "propagate": "no",
            }
        },
        "root": {"level": "DEBUG", "handlers": ["console", "log_file"]},
    }
    logging.config.dictConfig(logging_config)


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

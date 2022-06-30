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

import asyncio
import logging
from pathlib import Path
import sys
import click
from pydantic import BaseModel


logging.basicConfig()
logger: logging.Logger = logging.getLogger("worker")
logger.setLevel(logging.DEBUG)


class InvalidTokenError(Exception):
    """Token is invalid."""

    pass


class InvalidURLError(Exception):
    """Provided URL is invalid."""

    pass


class Config(BaseModel):
    """Represents the on-disk configuration for this worker."""

    queue_url: str
    scratch_dir: Path
    token: str

    def check_validity(self) -> None:
        if not self.scratch_dir.exists() or not self.scratch_dir.is_dir():
            raise NotADirectoryError()
        elif len(self.token) == 0:
            raise InvalidTokenError()
        elif len(self.queue_url) == 0:
            raise InvalidURLError()


class Worker:
    """
    Represents a worker. For now we have only one worker, which will perform
    tasks sequentially.
    """

    config: Config

    def __init__(self, config: Config) -> None:
        self.config = config

    def setup(self) -> None:
        """Setup this worker, including the scratch directory, ccache, etc."""
        pass

    def run(self) -> None:
        """Start worker's main loop"""
        logger.info("start worker")
        asyncio.run(self._run())

    async def _run(self) -> None:
        while True:
            logger.info("request work")
            await asyncio.sleep(5.0)


def _generate_config(path: Path) -> None:
    """Generate a configuration file."""
    config = Config(
        queue_url="https://tstr.coio.dev",
        scratch_dir=Path("/path/to/scratch"),
        token="mytoken",
    )
    path.write_text(config.json(indent=2))


@click.command()
@click.option(
    "-c",
    "--config",
    required=True,
    type=click.Path(file_okay=True, dir_okay=False),
    help="Config file location.",
)
@click.option(
    "--gen-config",
    is_flag=True,
    default=False,
    type=bool,
    help="Generate config at specified path.",
)
def cli(config: str, gen_config: bool):
    config_path = Path(config)
    if not config_path.exists():
        if gen_config:
            _generate_config(config_path)
            click.echo(f"Wrote default config to '{config}'")
            return
        click.echo(f"Error: config file not found at '{config}'")
        sys.exit(1)

    cfg: Config = Config.parse_file(config_path)
    click.echo(f"config = {cfg}")
    try:
        cfg.check_validity()
    except NotADirectoryError:
        click.echo("Error: scratch path does not exist or is not a directory")
        sys.exit(1)
    except InvalidTokenError:
        click.echo("Error: invalid token")
        sys.exit(1)
    except InvalidURLError:
        click.echo("Error: invalid queue URL.")
        sys.exit(1)

    worker = Worker(cfg)
    worker.setup()
    worker.run()


if __name__ == "__main__":
    cli()

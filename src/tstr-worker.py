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
import os
from pathlib import Path
import signal
import sys
from typing import List, Optional, Tuple
import click
from pydantic import BaseModel, parse_raw_as


logging.basicConfig()
logger: logging.Logger = logging.getLogger("worker")
logger.setLevel(logging.DEBUG)


class InvalidTokenError(Exception):
    """Token is invalid."""

    pass


class InvalidURLError(Exception):
    """Provided URL is invalid."""

    pass


class TstrError(Exception):
    """An error."""

    def __init__(self, msg: Optional[str] = None) -> None:
        self.msg = msg

    def __str__(self) -> str:
        if self.msg is not None:
            return self.msg
        return "an error occurred"


class GitError(TstrError):
    """Represents an error from a git command or action."""

    pass


async def run_cmd(args: List[str]) -> Tuple[int, Optional[str], Optional[str]]:
    """Run a command."""
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout: Optional[str] = None
    stderr: Optional[str] = None

    if proc.stdout:
        stdout = (await proc.stdout.read()).decode("utf-8")
    if proc.stderr:
        stderr = (await proc.stderr.read()).decode("utf-8")

    retcode = await asyncio.wait_for(proc.wait(), None)
    logger.debug(f"run {args}: retcode: {retcode}")

    return retcode, stdout, stderr


class PodmanImage(BaseModel):
    Id: str
    Names: List[str]


async def podman_exists(img: str, prefix: str = "localhost") -> bool:
    lst: List[str] = [
        "podman",
        "image",
        "list",
        "--format",
        "json",
        img,
    ]
    res, out, err = await run_cmd(lst)
    if res != 0:
        raise TstrError(f"unable to obtain podman images: {err}")
    elif out is None:
        raise TstrError("unexpected lack of output from image listing.")

    images: List[PodmanImage] = parse_raw_as(List[PodmanImage], out)
    for entry in images:
        if f"{prefix}/{img}" in entry.Names:
            return True
    return False


class Git:
    """Perform some basic tasks on a repository."""

    repo: str
    path: Path

    def __init__(self, repo: str, path: Path, logger: logging.Logger) -> None:
        self.repo = repo
        self.path = path
        self.logger = logger.getChild(f"git({self.repo})")

    async def clone(self, branch: Optional[str] = None) -> None:
        """
        Clone a git repository (from github) to a specified path, and clone
        checking out (optionally) a specified branch (alternatively, the
        repository's default.)
        """
        lst: List[str] = [
            "clone",
            f"https://github.com/{self.repo}",
            self.path.as_posix(),
        ]
        if branch is not None:
            lst.extend(["-b", branch])

        await self.run(lst, new=True)
        self.logger.info(
            f"cloned repository '{self.repo}' to "
            f"'{self.path} (branch: {branch})'"
        )

    async def update(self) -> None:
        """
        Update the repository's remotes and pull latest for the default branch.
        """
        await self.run(["remote", "update"])
        self.logger.debug("updated remotes")
        await self.run(["pull"])
        sha = (await self.get_sha()).strip()
        self.logger.debug(f"pulled latest version ({sha})")

    async def get_sha(self, short: bool = False) -> str:
        """Obtain repository's HEAD sha256"""
        lst: List[str] = ["rev-parse"]
        if short:
            lst.append("--short")
        lst.append("HEAD")
        res = await self.run(lst)
        if res is None:
            raise GitError(
                msg=f"unable to obtain HEAD version for repo at '{self.path}"
            )
        return res.strip()

    async def run(self, args: List[str], new: bool = False) -> Optional[str]:
        """
        Run a git command within the repository's path, unless we're cloning.
        """
        lst: List[str] = ["git"]
        if not new:
            lst.extend(["-C", self.path.as_posix()])
        lst.extend(args)

        ret, out, err = await run_cmd(lst)
        if ret != 0:
            raise GitError(msg=err)
        return out


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
    keep_running: bool

    def __init__(self, config: Config) -> None:
        self.config = config
        self.keep_running = True

    async def setup(self) -> None:
        """Setup this worker, including the scratch directory, ccache, etc."""
        pass

    async def run(self) -> None:
        """Start worker's main loop"""

        def _interrupt() -> None:
            self.keep_running = False

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, _interrupt)

        while self.keep_running:
            builder = CreateBuildContainer(self.config)
            logger.info("setup builder image")
            await builder.setup()
            await builder.run()

            logger.info("build s3gw")
            unit = CreateS3GWContainer(self.config)
            await unit.setup()
            await unit.run()

            logger.info("request work")
            await asyncio.sleep(5.0)


class CreateBuildContainer:
    """
    Creates a build container image from s3gw-core.git's latest main branch.
    """

    config: Config
    repo: Path
    git: Git

    def __init__(self, cfg: Config) -> None:
        self.config = cfg
        self.repo = cfg.scratch_dir.joinpath("s3gw-core.git")
        self.logger = logger.getChild("builder")
        self.git = Git("aquarist-labs/s3gw-core", self.repo, self.logger)

    async def setup(self) -> None:
        """Ensure we have an aquarist-labs/s3gw-core.git clone."""
        self.logger.debug(f"setup build container at '{self.repo}'")
        if self.repo.exists():
            if not self.repo.is_dir():
                raise TstrError(
                    msg=f"path at '{self.repo}' exists and is not a directory"
                )
            self.logger.debug(f"repository already exists at '{self.repo}'")
        else:
            await self.git.clone()
        # Update repository. If it is brand new, it's essentially a no-op;
        # otherwise update the existing repository.
        await self.git.update()

    async def run(self) -> None:
        """Build a docker image for an s3gw builder container."""
        build_dir = self.repo.joinpath("build")
        if not build_dir.exists() or not build_dir.is_dir():
            self.logger.error(
                f"unable to find build directory at '{self.repo}'"
            )
            raise NotADirectoryError()

        sha: str = await self.git.get_sha(short=True)
        img: str = f"tstr-s3gw-builder:{sha}"
        if await podman_exists(img):
            self.logger.info(f"found existing image '{img}', nothing to do.")
            return

        self.logger.info(f"building image '{img}'.")
        lst: List[str] = [
            "podman",
            "build",
            "-t",
            img,
            "-f",
            "Dockerfile.build-radosgw",
            build_dir.as_posix(),
        ]
        res, _, err = await run_cmd(lst)
        if res != 0:
            self.logger.error(f"unable to build image '{img}': {err}")
            raise TstrError()
        self.logger.info(f"created builder container '{img}'.")
        await run_cmd(["podman", "tag", img, "tstr-s3gw-builder:latest"])


class CreateS3GWContainer:
    """
    Creates an S3GW container image for a specified branch/sha from
    aquarist-labs/ceph.git, using the aquarist-labs/s3gw-core.git's build
    container.
    """

    config: Config
    cephdir: Path
    ccache: Path
    git: Git

    def __init__(self, cfg: Config) -> None:
        self.config = cfg
        self.cephdir = cfg.scratch_dir.joinpath("ceph.git")
        self.ccache = self.cephdir.joinpath("build.ccache")
        self.logger = logger.getChild("s3gw-builder")
        self.git = Git("aquarist-labs/ceph.git", self.cephdir, self.logger)
        pass

    async def setup(self) -> None:
        """
        Ensure we have an aquarist-labs/ceph.git clone, and a ready to go
        ccache.
        """
        self.logger.debug("setup radosgw build")
        if self.cephdir.exists():
            if not self.cephdir.is_dir():
                raise TstrError(
                    msg=f"path at '{self.cephdir}' exists and is not"
                    " a directory."
                )
            self.logger.debug(f"repository already exists at '{self.cephdir}'.")
        else:
            self.logger.debug(f"clone repository to '{self.cephdir}'.")
            await self.git.clone()
        await self.git.update()

        self.ccache.mkdir(exist_ok=True)
        ret, _, err = await run_cmd(
            ["ccache", "-d", self.ccache.as_posix(), "-M", "10G"]
        )
        if ret != 0:
            raise TstrError(
                msg=f"unable to init ccache at '{self.ccache}': {err}"
            )

        if not await podman_exists("tstr-s3gw-builder:latest"):
            raise TstrError(msg="missing s3gw builder image.")

        self.logger.info(f"setup radosgw build successfully.")

    async def run(self) -> None:
        """Build the radosgw binaries, and then the s3gw container."""

        sha: str = await self.git.get_sha(short=True)
        s3gw_img: str = f"tstr-s3gw:{sha}"
        if await podman_exists(s3gw_img):
            self.logger.info(f"found existing image {s3gw_img}, nothing to do.")
            return

        self.logger.debug("build radosgw")
        ret, _, err = await run_cmd(
            [
                "podman",
                "run",
                "--replace",
                "--name",
                "tstr-build-radosgw",
                "-v",
                f"{self.cephdir.as_posix()}:/srv/ceph",
                "localhost/tstr-s3gw-builder:latest",
            ]
        )
        if ret != 0:
            raise TstrError(msg=f"unable to build radosgw: {err}")

        # ensure the radosgw binary has been built
        builddir = self.cephdir.joinpath("build")
        radosgw = builddir.joinpath("bin", "radosgw")
        if not radosgw.exists():
            raise TstrError(msg=f"unable to find radosgw binary at {radosgw}.")

        s3gw_dockerfile = self.config.scratch_dir.joinpath(
            "s3gw-core.git", "build", "Dockerfile.build-container"
        )
        if not s3gw_dockerfile.exists():
            raise TstrError(
                msg=f"unable to find Dockerfile at {s3gw_dockerfile}"
            )

        self.logger.debug(f"create s3gw container for version {sha}.")
        ret, _, err = await run_cmd(
            [
                "podman",
                "build",
                "-t",
                s3gw_img,
                "-f",
                s3gw_dockerfile.as_posix(),
                builddir.as_posix(),
            ]
        )
        if ret != 0:
            raise TstrError(msg=f"error creating s3gw image {s3gw_img}: {err}")

        self.logger.info(f"created s3gw container image '{s3gw_img}'.")


class RunS3Tests:
    """
    Runs s3tests against a running S3GW container.
    """

    pass


def _generate_config(path: Path) -> None:
    """Generate a configuration file."""
    config = Config(
        queue_url="https://tstr.coio.dev",
        scratch_dir=Path("/path/to/scratch"),
        token="mytoken",
    )
    path.write_text(config.json(indent=2))


async def main(cfg: Config) -> None:
    worker = Worker(cfg)
    builder = CreateBuildContainer(cfg)
    main_loop = asyncio.create_task(worker.run())

    await asyncio.gather(worker.setup(), builder.setup())
    await asyncio.gather(main_loop)
    await main_loop
    logger.debug(os.getcwd())


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

    asyncio.run(main(cfg))


if __name__ == "__main__":
    cli()

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

import csv
import os
from pathlib import Path
import sys
import requests
import click
from datetime import datetime as dt
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel

from libtstr.benchmark import Op, OpResult, WarpCmd, Result


class Config(BaseModel):
    url: str
    token: str


def byte_to_SI(val: float) -> Tuple[float, str]:

    lst = ["B", "kB", "MB", "GB", "TB", "PB"]

    tmp = val
    idx = 0
    while int(tmp / 1000) > 0:
        tmp /= 1000
        idx += 1

    unit = lst[idx] if idx < len(lst) else "WHAT"
    return round(tmp, 2), unit


def handle_result(op: Op, total_ops: int) -> OpResult:

    dur = op.duration / 1000000000
    op_per_sec = round(op.count / dur, 2)
    obj_per_sec = round(op.num_objects / dur, 2)
    bytes_per_sec = int(round(op.num_bytes / dur))
    op_percent = round((op.count * 100) / total_ops)
    return OpResult(
        name=op.name,
        percent=op_percent,
        ops_per_sec=op_per_sec,
        objs_per_sec=obj_per_sec,
        bytes_per_sec=bytes_per_sec,
    )


def parse_warp_cmd(cmd: str) -> WarpCmd:
    assert cmd.startswith("#")
    # print(f"cmd: {cmd[2:]}")
    tokens: List[str] = cmd[2:].split()
    opts: List[str] = []
    pos: List[str] = []
    for tkn in tokens[1:]:
        if tkn.startswith("--"):
            opts.append(tkn)
        else:
            pos.append(tkn)

    duration: str = ""
    objsize: str = ""
    objects: int = 0

    for tkn in opts:
        opt, val = tkn.split("=")
        if opt == "--duration":
            duration = val
        elif opt == "--obj.size":
            objsize = val
        elif opt == "--objects":
            objects = int(val)

    return WarpCmd(
        workload=pos[0],
        duration=duration,
        objects=objects,
        objsize=objsize,
    )


def upload(url: str, token: str, res: Result) -> None:
    ep = f"{url}/api/bench/new"
    req = requests.put(
        ep,
        data=res.json(),
        headers={
            "Content-Type": "application/json",
            "X-Token": token,
        },
    )
    print(f"request result: {req}")
    print(req.json())
    assert res is not None
    assert req.status_code == 200
    print(f"uploaded result to {url}")


def main(file: Path, version: str, url: str, token: str):

    ops: Dict[str, Op] = {}
    total_ops = 0
    total_duration = 0
    warpcmd: Optional[WarpCmd] = None
    maxthreads: int = 0

    version = sys.argv[2]

    if token is None or url is None:
        print("please specify TSTR_REPORT_TOKEN and TSTR_REPORT_URL.")
        sys.exit(1)

    assert len(token) > 0
    assert len(url) > 0

    with open(file, newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        for row in reader:
            if row["thread"] is None:
                warpcmd = parse_warp_cmd(row["idx"])
                continue

            maxthreads = max(int(row["thread"]) + 1, maxthreads)
            total_ops += 1
            total_duration += int(row["duration_ns"]) / 1000000000

            try:
                # print(row)
                if row["op"] not in ops:
                    ops[row["op"]] = Op(
                        name=row["op"],
                        count=1,
                        duration=int(row["duration_ns"]),
                        num_objects=int(row["n_objects"]),
                        num_bytes=int(row["bytes"]),
                    )
                else:
                    op = ops[row["op"]]
                    op.count += 1
                    op.duration += int(row["duration_ns"])
                    op.num_objects += int(row["n_objects"])
                    op.num_bytes += int(row["bytes"])
            except TypeError as e:
                print("error occurred!")
                print(e)
                print("------ row ------")
                print(row)
                sys.exit(1)

    # print(ops)

    lst: List[OpResult] = []
    for op in ops.values():
        lst.append(handle_result(op, total_ops))

    assert warpcmd is not None
    assert maxthreads > 0
    result = Result(
        version=version,
        date=dt.utcnow(),
        duration=round(total_duration / maxthreads, 2),
        threads=maxthreads,
        details=warpcmd,
        ops=lst,
    )

    print(result.json(indent=2))
    upload(url, token, result)


@click.command()
@click.argument(
    "file",
    type=click.Path(file_okay=True, dir_okay=False),
    required=True,
)
@click.argument(
    "version",
    type=str,
    required=True,
)
@click.option(
    "-c",
    "--config",
    required=False,
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
def cli(
    file: str, version: str, config: Optional[str], gen_config: bool
) -> None:
    url: Optional[str] = None
    token: Optional[str] = None

    config_path = (
        Path(config) if config is not None else Path("tstr-report.cfg")
    )
    if not config_path.exists():
        if gen_config:
            newcfg = Config(url="http://127.0.0.1", token="asdfghj")
            config_path.write_text(newcfg.json(indent=2))
            click.echo(f"Wrote default config to '{config_path}")
            return
    else:
        cfg = Config.parse_file(config_path)
        url = cfg.url
        token = cfg.token

    url = os.getenv("TSTR_REPORT_URL", url)
    token = os.getenv("TSTR_REPORT_TOKEN", token)
    if url is None:
        click.echo(
            "Missing URL: specify via config file or TSTR_REPORT_URL"
            " env variable."
        )
        sys.exit(1)

    if token is None:
        click.echo(
            "Missing token: specify via config file or TSTR_REPORT_TOKEN "
            "env variable."
        )
        sys.exit(1)

    file_path = Path(file)
    assert file_path.exists()
    main(file_path, version, url, token)


if __name__ == "__main__":
    cli()

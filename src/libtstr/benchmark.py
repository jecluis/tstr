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

from typing import List
from datetime import datetime as dt
from pydantic import BaseModel


class Op(BaseModel):
    name: str
    count: int
    duration: int
    num_objects: int
    num_bytes: int


class OpResult(BaseModel):
    name: str
    percent: int
    ops_per_sec: float
    objs_per_sec: float
    bytes_per_sec: int


class WarpCmd(BaseModel):
    duration: str
    objects: int
    objsize: str
    workload: str


class Result(BaseModel):
    version: str
    date: dt
    threads: int
    duration: float
    details: WarpCmd
    ops: List[OpResult]

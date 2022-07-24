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

# pyright: reportGeneralTypeIssues=false
# pyright: reportIncompatibleVariableOverride=false
# pyright: reportUnknownMemberType=false

from datetime import datetime as dt
from typing import List, Optional
import ormar
from sqlalchemy import func
from pydantic.typing import ForwardRef

from libtstr.db import BaseMeta, engine


ThroughRef = ForwardRef("ResultToOpResult")


class User(ormar.Model):
    class Meta(BaseMeta):
        tablename = "users"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=1024)
    user: str = ormar.String(max_length=1024, unique=True)


class Host(ormar.Model):
    class Meta(BaseMeta):
        tablename = "hosts"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=1024, unique=True)
    cores: int = ormar.Integer()
    ram: int = ormar.Integer()


class Token(ormar.Model):
    class Meta(BaseMeta):
        tablename = "tokens"

    token: str = ormar.String(max_length=1024, primary_key=True)
    user: User = ormar.ForeignKey(User)
    host: Host = ormar.ForeignKey(Host)


class OpResult(ormar.Model):
    class Meta(BaseMeta):
        tablename = "benchmark_results_ops"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    # result: Result = ormar.ForeignKey(Result, related_name="ops")
    percent: int = ormar.Integer()
    ops_per_sec: float = ormar.Float()
    objs_per_sec: float = ormar.Float()
    bytes_per_sec: int = ormar.Integer()


class ResultToOpResult(ormar.Model):
    class Meta(BaseMeta):
        tablename = "benchmark_result_x_ops"

    id: int = ormar.Integer(primary_key=True)


class Result(ormar.Model):
    class Meta(BaseMeta):
        tablename = "benchmark_results"

    id: int = ormar.Integer(primary_key=True)
    # submitter: Token = ormar.ForeignKey(Token)
    version: str = ormar.String(max_length=1024)
    date: dt = ormar.DateTime(server_default=func.now())
    duration: float = ormar.Float()
    threads: int = ormar.Integer()
    workload: str = ormar.String(max_length=100)
    objsize: str = ormar.String(max_length=100)
    num_objects: int = ormar.Integer()
    duration_str: str = ormar.String(max_length=100)
    ops: Optional[List[OpResult]] = ormar.ManyToMany(
        OpResult, through=ResultToOpResult
    )


Result.update_forward_refs()

User.Meta.table.create(engine, checkfirst=True)
Host.Meta.table.create(engine, checkfirst=True)
Token.Meta.table.create(engine, checkfirst=True)
OpResult.Meta.table.create(engine, checkfirst=True)
Result.Meta.table.create(engine, checkfirst=True)
ResultToOpResult.Meta.table.create(engine, checkfirst=True)

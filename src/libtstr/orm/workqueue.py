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

from enum import Enum
from datetime import datetime as dt
import ormar
from sqlalchemy import func

from libtstr.db import BaseMeta, engine
from libtstr.orm.heads import Head


class JobTypeEnum(Enum):
    BUILD = 0
    S3TESTS = 1
    BENCHMARK = 2


class JobStateEnum(Enum):
    WAITING = 0
    RUNNING = 1
    FINISHED = 2


class WQStateEnum(Enum):
    NEW = 0
    ASSIGNED = 1
    RUNNING = 2
    DONE = 3


class Job(ormar.Model):
    class Meta(BaseMeta):
        tablename = "jobs"

    id: int = ormar.Integer(primary_key=True)
    head: Head = ormar.ForeignKey(Head)
    when: dt = ormar.DateTime(server_default=func.now())
    what: JobTypeEnum = ormar.Enum(enum_class=JobTypeEnum)
    state: JobStateEnum = ormar.Enum(enum_class=JobStateEnum)


class WQEntry(ormar.Model):
    class Meta(BaseMeta):
        tablename = "workqueue"

    id: int = ormar.Integer(primary_key=True)
    job: Job = ormar.ForeignKey(Job)  # type: ignore
    when: dt = ormar.DateTime(server_default=func.now())
    state: WQStateEnum = ormar.Enum(enum_class=WQStateEnum)


Job.Meta.table.create(engine, checkfirst=True)
WQEntry.Meta.table.create(engine, checkfirst=True)

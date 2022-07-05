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

import ormar
from datetime import datetime as dt
from enum import Enum
from sqlalchemy import func

from libtstr.db import BaseMeta, engine


class HeadStateEnum(Enum):
    NEW = 0
    CLOSED = 1


class TstrHead(ormar.Model):
    class Meta(BaseMeta):
        tablename = "heads"

    id: int = ormar.Integer(primary_key=True)
    sha: str = ormar.String(max_length=1024)
    head: str = ormar.String(max_length=1024)
    source: str = ormar.String(max_length=1024)
    is_pull_request: bool = ormar.Boolean(default=False)
    pr_id: int = ormar.Integer(default=-1)
    when: dt = ormar.DateTime(server_default=func.now())
    what: HeadStateEnum = ormar.Enum(enum_class=HeadStateEnum)


TstrHead.Meta.table.create(engine, checkfirst=True)

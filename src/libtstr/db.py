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

# pyright: reportUnknownMemberType=false

import databases
import sqlalchemy
from ormar import ModelMeta

_dburl = "sqlite:///tstr.db"

metadata = sqlalchemy.MetaData()
database = databases.Database(_dburl)
engine = sqlalchemy.create_engine(_dburl)


class BaseMeta(ModelMeta):
    database: databases.Database = database
    metadata: sqlalchemy.MetaData = metadata

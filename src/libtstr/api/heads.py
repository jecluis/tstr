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
from fastapi import APIRouter, Depends

# from fastapi.logger import logger

from libtstr.api import githubmgr
from libtstr.gh import GithubMgr, GithubBranch


router = APIRouter(prefix="/heads", tags=["heads"])


@router.get(
    "/", name="Obtain currently open heads.", response_model=List[GithubBranch]
)
async def get_heads(gh: GithubMgr = Depends(githubmgr)) -> List[GithubBranch]:
    return await gh.get_heads()

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

from fastapi import Request, Depends

from libtstr.state import TstrState
from libtstr.gh import GithubMgr
from libtstr.wq import WorkQueue


async def tstr_state(req: Request) -> TstrState:
    return req.app.state.tstr


async def githubmgr(state: TstrState = Depends(tstr_state)) -> GithubMgr:
    return state.github


async def workqueue(state: TstrState = Depends(tstr_state)) -> WorkQueue:
    return state.workqueue

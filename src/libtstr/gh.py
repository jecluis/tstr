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

import asyncio
from typing import List, Optional
import github
from pydantic import BaseModel
from fastapi.logger import logger

from libtstr.orm.heads import TstrHead, HeadStateEnum


class GithubConfig(BaseModel):
    token: str
    repo: str


class GithubHead(BaseModel):
    head: str
    source: str
    sha: str
    is_pull_request: bool
    id: Optional[int]
    state: Optional[str]


class GithubMgr:

    config: GithubConfig
    gh: github.Github
    repo: str
    _heads: List[GithubHead]
    _is_running: bool
    _task: Optional[asyncio.Task]  # type: ignore

    def __init__(self, config: GithubConfig) -> None:
        self.config = config
        self.gh = github.Github(config.token)
        self.repo = config.repo
        self._heads = []
        self._is_running = False
        self._task = None

    async def start(self):
        self._is_running = True
        self._task = asyncio.create_task(self._main_task())

    async def stop(self):
        self._is_running = False
        if self._task is not None:
            await self._task
            self._task = None

    async def _main_task(self) -> None:

        while self._is_running:
            logger.debug("updating github heads")
            # self._heads = await self._get_heads()
            await self._update_heads()

            await asyncio.sleep(30.0)

    async def _update_heads(self) -> None:
        logger.info("updating heads")
        heads = await self._get_heads()
        cnt_new: int = 0
        cnt_closed: int = 0
        cnt_skipped: int = 0
        for head in heads:
            entries = await TstrHead.objects.filter(
                ((TstrHead.sha == head.sha) & (TstrHead.head == head.head))
            ).all()
            if len(entries) == 0:
                # add new head
                new_head = TstrHead(
                    sha=head.sha,
                    head=head.head,
                    source=head.source,
                    is_pull_request=head.is_pull_request,
                    pr_id=(head.id if head.is_pull_request else -1),
                    what=HeadStateEnum.NEW,
                )
                await new_head.save()
                cnt_new = cnt_new + 1
                continue
            if head.state != "closed":
                # we don't care what state we are in then, just move on
                cnt_skipped = cnt_skipped + 1
                continue
            is_closed = False
            for entry in entries:
                if entry.what == HeadStateEnum.CLOSED:
                    is_closed = True
                    break
            if not is_closed:
                # add new head, mark it closed.
                new_head = TstrHead(
                    sha=head.sha,
                    head=head.head,
                    source=head.source,
                    is_pull_request=head.is_pull_request,
                    pr_id=(head.id if head.is_pull_request else -1),
                    what=HeadStateEnum.CLOSED,
                )
                await new_head.save()
                cnt_closed = cnt_closed + 1

        logger.info(
            f"new: {cnt_new}, closed: {cnt_closed}, skipped: {cnt_skipped}"
        )

    async def _get_heads(self) -> List[GithubHead]:
        heads: List[GithubHead] = []

        repo = self.gh.get_repo(self.repo)
        default_branch = repo.get_branch(repo.default_branch)
        sha: str = default_branch.commit.sha

        heads.append(
            GithubHead(
                head=default_branch.name,
                source=default_branch.name,
                sha=sha,
                is_pull_request=False,
                id=None,
                state=None,
            )
        )

        pulls = repo.get_pulls()
        for pr in pulls:
            heads.append(
                GithubHead(
                    head=f"pull/{pr.number}/head",
                    source=pr.head.label,
                    sha=pr.head.sha,
                    is_pull_request=True,
                    id=pr.number,
                    state=pr.state,
                )
            )

        return heads

    async def get_heads(self) -> List[GithubHead]:
        heads: List[GithubHead] = []
        db_heads = await TstrHead.objects.all()
        for head in db_heads:
            pr_id: Optional[int] = head.pr_id if head.pr_id > 0 else None
            pr_state: str = (
                "open" if head.what != HeadStateEnum.CLOSED else "closed"
            )
            heads.append(
                GithubHead(
                    head=head.head,
                    source=head.source,
                    sha=head.sha,
                    is_pull_request=head.is_pull_request,
                    id=pr_id,
                    state=pr_state,
                )
            )
        return heads

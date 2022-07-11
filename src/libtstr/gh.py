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
from typing import Dict, List, Optional
from datetime import datetime as dt
import github
from pydantic import BaseModel
from fastapi.logger import logger

from libtstr.orm.heads import Branch, Head


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


class GithubCommit(BaseModel):
    sha: str
    when: dt


class GithubBranch(BaseModel):
    name: str
    source: str
    commits: List[GithubCommit]
    is_pull_request: bool
    id: Optional[int]
    state: str


class GithubMgr:

    config: GithubConfig
    gh: github.Github
    repo: str
    _heads: List[Head]
    _branches: List[Branch]
    _branches_by_name: Dict[str, Branch]
    _heads_by_sha: Dict[str, List[Head]]
    _is_running: bool
    _task: Optional[asyncio.Task]  # type: ignore

    def __init__(self, config: GithubConfig) -> None:
        self.config = config
        self.gh = github.Github(config.token)
        self.repo = config.repo
        self._heads = []
        self._branches = []
        self._branches_by_name = {}
        self._heads_by_sha = {}
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

        await self._load()

        while self._is_running:
            logger.debug("updating github heads")
            # self._heads = await self._get_heads()
            await self._update_heads()

            await asyncio.sleep(30.0)

    async def _load(self) -> None:
        self._heads = await Head.objects.all()
        self._branches = await Branch.objects.all()

        for b in self._branches:
            assert b.name not in self._branches_by_name
            self._branches_by_name[b.name] = b

        for h in self._heads:
            if h.sha not in self._heads_by_sha:
                self._heads_by_sha[h.sha] = []
            self._heads_by_sha[h.sha].append(h)

    async def _update_heads(self) -> None:

        skipped = 0
        new_heads = 0
        new_branches = 0
        closed_branches = 0
        reopened_branches = 0

        gh_heads = await self._get_heads()
        for ghead in gh_heads:
            if ghead.head in self._branches_by_name:

                existing: Branch = self._branches_by_name[ghead.head]
                if existing.is_closed:
                    # what we have is closed, check if we need to open it.
                    if ghead.state != "closed":
                        existing.is_closed = False
                        await existing.update()
                        reopened_branches += 1
                    else:
                        # skip ahead
                        skipped += 1
                        continue

                if ghead.sha in self._heads_by_sha:
                    found = False
                    for h in self._heads_by_sha[ghead.sha]:
                        if h.branch.name == ghead.head:
                            found = True
                            break
                    if found:
                        # head/sha already tracked
                        skipped += 1
                        continue
                    else:
                        # new sha for branch/PR
                        new_head = Head(
                            sha=ghead.sha,
                            branch=existing,
                        )
                        self._heads_by_sha[ghead.sha].append(new_head)
                        self._heads.append(new_head)
                        await new_head.save()
                        new_heads += 1
                else:
                    # new head for branch/PR
                    new_head = Head(
                        sha=ghead.sha,
                        branch=existing,
                    )
                    self._heads.append(new_head)
                    self._heads_by_sha[ghead.sha] = [new_head]
                    await new_head.save()
                    new_heads += 1

                if ghead.state == "closed":
                    existing.is_closed = True
                    await existing.update()
                    closed_branches += 1
            else:
                # new branch/PR
                #
                if ghead.state == "closed":
                    # ignore closed PRs if they are new to us
                    skipped += 1
                    continue

                new_branch = Branch(
                    name=ghead.head,
                    source=ghead.source,
                    is_pull_request=ghead.is_pull_request,
                    pr_id=(-1 if not ghead.is_pull_request else ghead.id),
                    is_closed=False,
                )
                new_head = Head(
                    sha=ghead.sha,
                    branch=new_branch,
                )
                self._branches.append(new_branch)
                self._branches_by_name[new_branch.name] = new_branch
                self._heads.append(new_head)
                if new_head.sha not in self._heads_by_sha:
                    self._heads_by_sha[new_head.sha]
                self._heads_by_sha[new_head.sha].append(new_head)
                await new_branch.save()
                await new_head.save()
                new_branches += 1
                new_heads += 1

            pass

        logger.info(
            f"new(branches: {new_branches}, heads: {new_heads}), "
            f"skipped: {skipped}, closed: {closed_branches}, "
            f"reopened: {reopened_branches}"
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

    async def get_heads(self) -> List[GithubBranch]:
        heads: List[GithubBranch] = []

        for b in await Branch.objects.all():
            commits: List[GithubCommit] = []
            for h in await Head.objects.all(Head.branch.name == b.name):
                commits.append(GithubCommit(sha=h.sha, when=h.when))
            heads.append(
                GithubBranch(
                    name=b.name,
                    source=b.source,
                    commits=commits,
                    is_pull_request=b.is_pull_request,
                    id=(None if not b.is_pull_request else b.pr_id),
                    state=("closed" if b.is_closed else "open"),
                )
            )
        return heads

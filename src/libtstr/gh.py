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

from typing import List, Optional
import github
from pydantic import BaseModel


class GithubHead(BaseModel):
    head: str
    source: str
    sha: str
    is_pull_request: bool
    id: Optional[int]


class GithubMgr:

    gh: github.Github
    repo: str

    def __init__(self, repo: str) -> None:
        self.gh = github.Github()
        self.repo = repo

    async def get_heads(self) -> List[GithubHead]:
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
            )
        )

        pulls = repo.get_pulls(state="open")
        for pr in pulls:
            heads.append(
                GithubHead(
                    head=f"pull/{pr.number}/head",
                    source=pr.head.label,
                    sha=pr.head.sha,
                    is_pull_request=True,
                    id=pr.number,
                )
            )

        return heads

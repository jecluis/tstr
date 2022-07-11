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
from datetime import datetime as dt
from typing import List, Optional
from fastapi.logger import logger
from pydantic import BaseModel

from libtstr.orm.heads import Head
from libtstr.orm.workqueue import (
    Job,
    JobStateEnum,
    JobTypeEnum,
    WQEntry,
    WQStateEnum,
)


class WQJob(BaseModel):
    id: int
    sha: str
    branch: str
    when: dt
    what: str
    state: str


class WQItem(BaseModel):
    id: int
    job: WQJob
    when: dt
    state: str


class WorkQueue:

    _jobs: List[Job]
    _wq: List[WQEntry]
    _is_running: bool
    _task: Optional[asyncio.Task]  # type: ignore

    def __init__(self) -> None:
        self._jobs = []
        self._wq = []
        self._is_running = False
        self._task = None

    def start(self) -> None:
        self._is_running = True
        self._task = asyncio.create_task(self._main_task())

    async def stop(self) -> None:
        self._is_running = False
        if self._task is not None:
            await self._task
            self._task = None

    async def _main_task(self) -> None:
        await self._load()
        while self._is_running:
            logger.debug("updating workqueue")
            await self._update()
            await asyncio.sleep(10.0)

    async def _load(self) -> None:
        self._jobs = await Job.objects.all()
        self._wq = await WQEntry.objects.all()

    async def _update(self) -> None:
        # go through heads and create jobs where appropriate
        for head in await Head.objects.all():
            jobs = await Job.objects.all(Job.head.sha == head.sha)
            assert len(jobs) <= 1
            if len(jobs) > 0:
                # job already exists, continue
                continue
            # create new job
            job = Job(
                head=head,
                what=JobTypeEnum.BUILD,
                state=JobStateEnum.WAITING,
            )
            await job.save()
            # add wq entry
            entry = WQEntry(
                job=job,
                state=WQStateEnum.NEW,
            )
            await entry.save()
            logger.debug(
                f"created job for head(name: {head.branch.name}, "
                f"sha: {head.sha})"
            )
        pass

    async def get_entries(self) -> List[WQItem]:
        items: List[WQItem] = []

        def _job_what(what: JobTypeEnum) -> str:
            if what == JobTypeEnum.BUILD:
                return "build"
            elif what == JobTypeEnum.S3TESTS:
                return "s3tests"
            elif what == JobTypeEnum.BENCHMARK:
                return "benchmark"
            return "unknown"

        def _job_state(state: JobStateEnum) -> str:
            if state == JobStateEnum.WAITING:
                return "waiting"
            elif state == JobStateEnum.RUNNING:
                return "running"
            elif state == JobStateEnum.FINISHED:
                return "finished"
            return "unknown"

        def _entry_state(state: WQStateEnum) -> str:
            if state == WQStateEnum.NEW:
                return "new"
            elif state == WQStateEnum.ASSIGNED:
                return "assigned"
            elif state == WQStateEnum.RUNNING:
                return "running"
            elif state == WQStateEnum.DONE:
                return "done"
            return "unknown"

        for entry in await WQEntry.objects.all():
            print(f"entry: {entry}")
            await entry.job.load()
            await entry.job.head.load()
            await entry.job.head.branch.load()
            items.append(
                WQItem(
                    id=entry.id,
                    job=WQJob(
                        id=entry.job.id,
                        sha=entry.job.head.sha,
                        branch=entry.job.head.branch.name,
                        when=entry.job.when,
                        what=_job_what(entry.job.what),
                        state=_job_state(entry.job.state),
                    ),
                    when=entry.when,
                    state=_entry_state(entry.state),
                )
            )

        return items

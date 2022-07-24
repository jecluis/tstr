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
from datetime import datetime as dt
from fastapi import APIRouter, Depends
from fastapi.logger import logger
from pydantic import BaseModel

from libtstr.api import access_token_required
from libtstr.benchmark import OpResult, Result
from libtstr.orm import bench as orm


router = APIRouter(prefix="/bench", tags=["benchmark"])


class NewResultReply(BaseModel):
    id: int


@router.put(
    "/new",
    name="Add new benchmark result.",
    response_model=NewResultReply,
    dependencies=[Depends(access_token_required)],
)
async def add_new(result: Result) -> NewResultReply:

    new_entry = await orm.Result.objects.create(
        version=result.version,
        date=result.date,
        duration=result.duration,
        threads=result.threads,
        workload=result.details.workload,
        objsize=result.details.objsize,
        num_objects=result.details.objects,
        duration_str=result.details.duration,
    )

    for op in result.ops:
        new_op = await orm.OpResult.objects.create(
            name=op.name,
            percent=op.percent,
            ops_per_sec=op.ops_per_sec,
            objs_per_sec=op.objs_per_sec,
            bytes_per_sec=op.bytes_per_sec,
        )
        await new_entry.ops.add(new_op)  # type: ignore

    return NewResultReply(id=new_entry.id)


class ResultEntry(BaseModel):
    id: int
    version: str
    date: dt
    duration: float
    threads: int
    workload: str
    objsize: str
    objects: int
    duration_str: str
    ops: List[OpResult]


@router.get(
    "/results",
    name="Obtain existing benchmark results.",
    response_model=List[ResultEntry],
)
async def get_results() -> List[ResultEntry]:
    # lst: List[ResultReply] = []
    results: List[ResultEntry] = []
    lst = await orm.Result.objects.select_related("ops").all()  # type: ignore
    for entry in lst:

        opslst: List[OpResult] = []
        if entry.ops is not None:
            for op in entry.ops:
                opslst.append(
                    OpResult(
                        name=op.name,
                        percent=op.percent,
                        ops_per_sec=op.ops_per_sec,
                        objs_per_sec=op.objs_per_sec,
                        bytes_per_sec=op.bytes_per_sec,
                    )
                )

        results.append(
            ResultEntry(
                id=entry.id,
                version=entry.version,
                date=entry.date,
                duration=entry.duration,
                threads=entry.threads,
                workload=entry.workload,
                objsize=entry.objsize,
                objects=entry.num_objects,
                duration_str=entry.duration_str,
                ops=opslst,
            )
        )

    return results

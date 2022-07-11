/* 
 * tstr - testing stuff
 * Copyright (C) 2022 SUSE LLC
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 */
import { Component, OnDestroy, OnInit } from '@angular/core';
import { catchError, EMPTY, finalize, Observable, Subscription, take, timer } from 'rxjs';
import {
  BranchEntry,
  CommitEntry,
  HeadsService
} from 'src/app/shared/services/api/heads.service';
import { BenchmarkEnum, CommitStatusEntry, StateEnum, StatusEntry } from './status-page.types';

@Component({
  selector: 'tstr-status-page',
  templateUrl: './status-page.component.html',
  styleUrls: ['./status-page.component.scss']
})
export class StatusPageComponent implements OnInit, OnDestroy {

  entries: StatusEntry[] = [
    {
      name: "s3gw",
      type: "branch",
      commits: [],
      state: StateEnum.Done,
    },
    {
      name: "foo bar",
      type: "pr",
      commits: [],
      state: StateEnum.Done,
    },
    {
      name: "baz",
      type: "pr",
      commits: [],
      state: StateEnum.Running,
    }
  ];

  private headsData: Observable<BranchEntry[]>;
  private headsSubscription?: Subscription;
  private timerSubscription?: Subscription;

  constructor(private svc: HeadsService) {
    this.headsData = svc.getHeads();
  }

  ngOnInit(): void {
    this.reloadHeads();
  }

  ngOnDestroy(): void {
    this.timerSubscription?.unsubscribe();
    this.headsSubscription?.unsubscribe();
  }

  private reloadHeads(): void {
    this.headsSubscription = this.headsData
      .pipe(
        catchError((err) => {
          console.error("error loading heads data: ", err);
          return EMPTY;
        }),
        finalize(() => {
          this.timerSubscription = timer(30000)
            .pipe(take(1))
            .subscribe(() => {
              this.headsSubscription!.unsubscribe();
              this.reloadHeads();
            });
        })
      )
      .subscribe((data: BranchEntry[]) => {
        let entries: StatusEntry[] = [];
        data.forEach((entry => {
          let entryType: "pr" | "branch" = 
            (entry.is_pull_request ? "pr" : "branch");
          let entryName = entry.name;
          if (entry.is_pull_request) {
            entryName = `${entry.source} (#${entry.id})`;
          }
          let commits: CommitStatusEntry[] = [];
          entry.commits.forEach((c: CommitEntry) => {
            commits.push({ sha: c.sha });
          });
          entries.push({
            name: entryName,
            state: StateEnum.Scheduled,
            type: entryType,
            commits: commits,
          });
        }));
        this.entries = entries;
      });
  }

}

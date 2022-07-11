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
import {
  catchError,
  EMPTY,
  finalize,
  Observable,
  Subscription,
  take,
  timer
} from 'rxjs';
import {
  BranchEntry,
  CommitEntry,
  HeadsService
} from 'src/app/shared/services/api/heads.service';
import { WorkqueueService, WQItem } from 'src/app/shared/services/api/workqueue.service';
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
  private headsTimerSubscription?: Subscription;

  private wqData: Observable<WQItem[]>;
  private wqSubscription?: Subscription;
  private wqTimerSubscription?: Subscription;

  public wqItems: WQItem[] = [];

  constructor(
    private headsSvc: HeadsService,
    private wqSvc: WorkqueueService
  ) {
    this.headsData = headsSvc.getHeads();
    this.wqData = wqSvc.getItems();
  }

  ngOnInit(): void {
    this.reloadHeads();
    this.reloadWorkqueue();
  }

  ngOnDestroy(): void {
    this.headsTimerSubscription?.unsubscribe();
    this.headsSubscription?.unsubscribe();
    this.wqTimerSubscription?.unsubscribe();
    this.wqSubscription?.unsubscribe();
  }

  private reloadHeads(): void {
    this.headsSubscription = this.headsData
      .pipe(
        catchError((err) => {
          console.error("error loading heads data: ", err);
          return EMPTY;
        }),
        finalize(() => {
          this.headsTimerSubscription = timer(30000)
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

  private reloadWorkqueue(): void {
    this.wqSubscription = this.wqData
      .pipe(
        catchError((err) => {
          console.error("error loading workqueue data: ", err);
          return EMPTY;
        }),
        finalize(() => {
          this.wqTimerSubscription = timer(10000)
            .pipe(take(1))
            .subscribe(() => {
              this.wqSubscription!.unsubscribe();
              this.reloadWorkqueue();
            });
        })
      )
      .subscribe((data: WQItem[]) => {
        this.wqItems = data;
      });
  }

}

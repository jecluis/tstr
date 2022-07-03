import { Component, OnDestroy, OnInit } from '@angular/core';
import { catchError, EMPTY, finalize, Observable, Subscription, take, timer } from 'rxjs';
import { HeadEntry, HeadsService } from 'src/app/shared/services/api/heads.service';
import { BenchmarkEnum, StateEnum, StatusEntry } from './status-page.types';

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
      benchmark: BenchmarkEnum.Baseline,
      s3testsPercent: 50,
      lastUpdated: new Date(),
      state: StateEnum.Done,
    },
    {
      name: "foo bar",
      type: "pr",
      benchmark: BenchmarkEnum.AboveBaseline,
      s3testsPercent: 55,
      lastUpdated: new Date(),
      state: StateEnum.Done,
    },
    {
      name: "baz",
      type: "pr",
      benchmark: undefined,
      s3testsPercent: undefined,
      lastUpdated: undefined,
      state: StateEnum.Running,
    }
  ];

  private headsData: Observable<HeadEntry[]>;
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
      .subscribe((data: HeadEntry[]) => {
        let entries: StatusEntry[] = [];
        data.forEach((entry => {
          let entryType: "pr" | "branch" = 
            (entry.is_pull_request ? "pr" : "branch");
          let entryName = entry.source;
          if (entry.is_pull_request) {
            entryName = `${entry.source} (#${entry.id})`;
          }
          entries.push({
            name: entryName,
            state: StateEnum.Scheduled,
            type: entryType,
          });
        }));
        this.entries = entries;
      });
  }

}

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
import { BenchmarkService, BenchOpResult, BenchResult } from 'src/app/shared/services/api/benchmark.service';


type TestResult = {
  result: BenchResult;
  ops: {[id: string]: BenchOpResult};
};


type TestType = {
  workload: string;
  num_objects: number;
  object_size: string;
  duration: string;
  entries: TestResult[];
};


@Component({
  selector: 'tstr-benchmark-results',
  templateUrl: './benchmark-results.component.html',
  styleUrls: ['./benchmark-results.component.scss']
})
export class BenchmarkResultsComponent implements OnInit, OnDestroy {

  private resultsData: Observable<BenchResult[]>;
  private resultsSubscription?: Subscription;
  private resultsTimerSubscription?: Subscription;

  public results: BenchResult[] = [];
  public per_test_type: {[id: string]: TestType} = {};

  public constructor(private benchSvc: BenchmarkService) {
    this.resultsData = benchSvc.getResults();
  }

  public ngOnInit(): void {
    this.reloadResults();
  }

  public ngOnDestroy(): void {
    this.resultsTimerSubscription?.unsubscribe();
    this.resultsSubscription?.unsubscribe();
  }

  private updateResults(data: BenchResult[]): void {

    const per_test_type: {[id: string]: TestType} = {};
    data.forEach((res: BenchResult) => {
      const typestr = 
        `${res.workload}-${res.objsize}-${res.objects}-${res.duration_str}`;

      if (!(typestr in per_test_type)) {
        per_test_type[typestr] = {
          workload: res.workload,
          object_size: res.objsize,
          num_objects: res.objects,
          duration: res.duration_str,
          entries: [],
        };
      }
      const entry: TestResult = {
        result: res,
        ops: {},
      };

      res.ops.forEach((op: BenchOpResult) => {
        entry.ops[op.name.toLowerCase()] = op;
      });

      per_test_type[typestr].entries.push(entry);
    });

    this.per_test_type = per_test_type;
    this.results = data;
  }

  private reloadResults(): void {
    this.resultsSubscription = this.resultsData
      .pipe(
        catchError((err) => {
          console.error("error loading benchmark results: ", err);
          return EMPTY;
        }),
        finalize(() => {
          this.resultsTimerSubscription = timer(30000)
            .pipe(take(1))
            .subscribe(() => {
              this.resultsSubscription!.unsubscribe();
              this.reloadResults();
            });
        })
      )
      .subscribe((data: BenchResult[]) => {
        this.updateResults(data);
      });
  }

  public toSI(value: number): string {
    const units = ["B", "kB", "MB", "GB", "TB", "PB", "WOOT"];

    let tmp = value;
    let idx = 0;
    while (Math.floor(tmp / 1000) > 0) {
      tmp /= 1000;
      idx += 1;
    }

    const v = Math.round((tmp + Number.EPSILON) * 100) / 100;
    return `${v} ${units[idx]}`;
  }

  public hasOp(res: TestResult, name: string): boolean {
    return (name in res.ops);
  }

}

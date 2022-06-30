import { Component, OnInit } from '@angular/core';
import { BenchmarkEnum, StateEnum, StatusEntry } from './status-page.service';

@Component({
  selector: 'tstr-status-page',
  templateUrl: './status-page.component.html',
  styleUrls: ['./status-page.component.scss']
})
export class StatusPageComponent implements OnInit {

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

  constructor() { }

  ngOnInit(): void {
  }

}

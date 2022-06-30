import { Component, Input, OnInit } from '@angular/core';
import { BenchmarkEnum, StateEnum, StatusEntry } from '../status-page.service';

@Component({
  selector: 'tstr-status-card',
  templateUrl: './status-card.component.html',
  styleUrls: ['./status-card.component.scss']
})
export class StatusCardComponent implements OnInit {

  @Input() entry?: StatusEntry = undefined;
  constructor() { }

  ngOnInit(): void {
  }

  isBaseline(): boolean {
    return this.entry?.benchmark === BenchmarkEnum.Baseline;
  }

  isAboveBaseline(): boolean {
    return this.entry?.benchmark === BenchmarkEnum.AboveBaseline;
  }

  isBelowBaseline(): boolean {
    return this.entry?.benchmark === BenchmarkEnum.BelowBaseline;
  }

  isDone(): boolean {
    return this.entry?.state === StateEnum.Done;
  }

  isRunning(): boolean {
    return this.entry?.state === StateEnum.Running;
  }

  isScheduled(): boolean {
    return this.entry?.state === StateEnum.Scheduled;
  }
}

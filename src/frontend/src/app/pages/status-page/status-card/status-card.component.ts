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
import { Component, Input, OnInit } from '@angular/core';
import { BenchmarkEnum, StateEnum, StatusEntry } from '../status-page.types';

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

  // isBaseline(): boolean {
  //   return this.entry?.benchmark === BenchmarkEnum.Baseline;
  // }

  // isAboveBaseline(): boolean {
  //   return this.entry?.benchmark === BenchmarkEnum.AboveBaseline;
  // }

  // isBelowBaseline(): boolean {
  //   return this.entry?.benchmark === BenchmarkEnum.BelowBaseline;
  // }

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

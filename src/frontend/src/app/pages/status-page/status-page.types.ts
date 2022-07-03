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

export enum BenchmarkEnum {
  None = 0,
  Baseline = 1,
  AboveBaseline = 2,
  BelowBaseline = 3,
}

export enum StateEnum {
  Done = 0,
  Running = 1,
  Scheduled = 2,
}

export type StatusEntry = {
  name: string;
  type: "branch" | "pr";
  benchmark?: BenchmarkEnum;
  s3testsPercent?: number;
  lastUpdated?: Date;
  state: StateEnum;
};
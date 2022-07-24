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
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';


export type BenchOpResult = {
  name: string;
  percent: number;
  ops_per_sec: number;
  objs_per_sec: number;
  bytes_per_sec: number;
};


export type BenchResult = {
  id: number;
  version: string;
  date: Date;
  duration: number;
  duration_str: string;
  threads: number;
  workload: string;
  objsize: string;
  objects: number;
  ops: BenchOpResult[];
};


@Injectable({
  providedIn: 'root'
})
export class BenchmarkService {

  constructor(private http: HttpClient) { }

  getResults(): Observable<BenchResult[]> {
    return this.http.get<BenchResult[]>("/api/bench/results");
  }
}

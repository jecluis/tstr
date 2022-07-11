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


export type CommitEntry = {
  sha: string;
  when: Date;
};

export type BranchEntry = {
  name: string;
  source: string;
  commits: CommitEntry[];
  is_pull_request: boolean;
  id?: number;
  state: string;
};

@Injectable({
  providedIn: 'root'
})
export class HeadsService {

  constructor(private http: HttpClient) { }

  getHeads(): Observable<BranchEntry[]> {
    return this.http.get<BranchEntry[]>("/api/heads/");
  }
}

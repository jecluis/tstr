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


export type HeadEntry = {
  head: string;
  source: string;
  sha: string;
  is_pull_request: boolean;
  id?: number;
};

@Injectable({
  providedIn: 'root'
})
export class HeadsService {

  constructor(private http: HttpClient) { }

  getHeads(): Observable<HeadEntry[]> {
    return this.http.get<HeadEntry[]>("/api/heads/");
  }
}

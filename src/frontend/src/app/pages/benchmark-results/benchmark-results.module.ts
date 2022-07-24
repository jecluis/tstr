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
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { BenchmarkResultsRoutingModule } from './benchmark-results-routing.module';
import { BenchmarkResultsComponent } from './benchmark-results.component';



@NgModule({
  declarations: [
    BenchmarkResultsComponent,
  ],
  imports: [
    CommonModule,
    BenchmarkResultsRoutingModule,
  ]
})
export class BenchmarkResultsModule { }

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
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path: "status",
    loadChildren: () => 
      import("./pages/status-page/status-page.module")
      .then(m => m.StatusPageModule),
  },
  {
    path: "benchmark",
    loadChildren: () =>
      import("./pages/benchmark-results/benchmark-results.module")
      .then(m => m.BenchmarkResultsModule),
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes, { useHash: true })],
  exports: [RouterModule]
})
export class AppRoutingModule { }

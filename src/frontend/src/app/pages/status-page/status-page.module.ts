import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { StatusPageRoutingModule } from './status-page-routing.module';
import { StatusPageComponent } from './status-page.component';
import { StatusCardComponent } from './status-card/status-card.component';


@NgModule({
  declarations: [
    StatusPageComponent,
    StatusCardComponent
  ],
  imports: [
    CommonModule,
    StatusPageRoutingModule
  ]
})
export class StatusPageModule { }

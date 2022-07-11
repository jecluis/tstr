import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkqueueCardComponent } from './workqueue-card.component';

describe('WorkqueueCardComponent', () => {
  let component: WorkqueueCardComponent;
  let fixture: ComponentFixture<WorkqueueCardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ WorkqueueCardComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(WorkqueueCardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

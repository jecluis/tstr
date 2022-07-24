import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BenchmarkResultsComponent } from './benchmark-results.component';

describe('BenchmarkResultsComponent', () => {
  let component: BenchmarkResultsComponent;
  let fixture: ComponentFixture<BenchmarkResultsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ BenchmarkResultsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(BenchmarkResultsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

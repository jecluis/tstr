import { TestBed } from '@angular/core/testing';

import { WorkqueueService } from './workqueue.service';

describe('WorkqueueService', () => {
  let service: WorkqueueService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(WorkqueueService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});

import { TestBed } from '@angular/core/testing';

import { HeadsService } from './heads.service';

describe('HeadsService', () => {
  let service: HeadsService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(HeadsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { API_CONFIG } from '../config/api.config';
import { DecisionSupportReport } from '../models/decision-support.model';

@Injectable({ providedIn: 'root' })
export class DecisionSupportApiService {
  private readonly http = inject(HttpClient);

  getReport(cameraId: string, windowMinutes = 30) {
    return this.http.get<DecisionSupportReport>(
      `${API_CONFIG.orchestratorBaseUrl}/api/reports/decision-support`,
      {
        params: {
          cameraId,
          windowMinutes,
        },
      },
    );
  }
}

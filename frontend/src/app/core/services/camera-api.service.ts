import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { API_CONFIG } from '../config/api.config';
import { CameraRequirements, CameraViewModel } from '../models/camera.model';
import { CameraTelemetry } from '../models/telemetry.model';

@Injectable({ providedIn: 'root' })
export class CameraApiService {
  private readonly http = inject(HttpClient);

  getCameras() {
    return this.http.get<CameraViewModel[]>(
      `${API_CONFIG.orchestratorBaseUrl}/api/cameras`,
    );
  }

  updateRequirements(cameraId: string, payload: CameraRequirements) {
    return this.http.put<CameraViewModel>(
      `${API_CONFIG.orchestratorBaseUrl}/api/cameras/${cameraId}/requirements`,
      payload,
    );
  }

  getTelemetry(cameraId: string) {
    return this.http.get<CameraTelemetry>(
      `${API_CONFIG.orchestratorBaseUrl}/api/cameras/${cameraId}/telemetry`,
    );
  }

  updateStatus(cameraId: string, enabled: boolean) {
    // Tekrar .NET orkestratore yonlendiriyoruz. 
    // .NET hem kendi registry'sini guncelleyecek hem de Python'a iletecek.
    return this.http.put(
      `${API_CONFIG.orchestratorBaseUrl}/api/cameras/${cameraId}/status?enabled=${enabled}`,
      {}
    );
  }
}

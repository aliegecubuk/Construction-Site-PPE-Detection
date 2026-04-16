import { DestroyRef, Injectable, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError, of } from 'rxjs';

import { ViolationAlert } from '../models/alert.model';
import { CameraRequirements, CameraViewModel } from '../models/camera.model';
import { DecisionSupportReport } from '../models/decision-support.model';
import { CameraTelemetry, TelemetrySeverity } from '../models/telemetry.model';
import { AlertSignalrService } from './alert-signalr.service';
import { CameraApiService } from './camera-api.service';
import { DecisionSupportApiService } from './decision-support-api.service';

@Injectable({ providedIn: 'root' })
export class DashboardStateService {
  private readonly cameraApiService = inject(CameraApiService);
  private readonly alertSignalrService = inject(AlertSignalrService);
  private readonly decisionSupportApiService = inject(DecisionSupportApiService);
  private readonly destroyRef = inject(DestroyRef);

  private telemetryTimer?: number;
  private reportTimer?: number;
  private cameraRetryTimer?: number;
  private signalrRetryTimer?: number;
  private signalrInitialized = false;
  private initialized = false;

  readonly cameras = signal<CameraViewModel[]>([]);
  readonly selectedCameraId = signal<string>('');
  readonly liveAlerts = signal<ViolationAlert[]>([]);
  readonly telemetry = signal<CameraTelemetry | null>(null);
  readonly decisionSupport = signal<DecisionSupportReport | null>(null);
  readonly errorMessage = signal<string>('');

  // Sadece aktif olan kameraları takip et
  readonly activeCamerasCount = computed(() => {
    return this.cameras().filter(c => c.enabled).length;
  });

  readonly filteredAlerts = computed(() => {
    const selectedCameraId = this.selectedCameraId();
    return this.liveAlerts().filter((alert) => alert.cameraId === selectedCameraId);
  });

  readonly latestAlerts = computed(() => this.filteredAlerts().slice(0, 6));

  constructor() {
    this.destroyRef.onDestroy(() => {
      if (this.telemetryTimer) {
        window.clearInterval(this.telemetryTimer);
      }
      if (this.reportTimer) {
        window.clearInterval(this.reportTimer);
      }
      if (this.cameraRetryTimer) {
        window.clearInterval(this.cameraRetryTimer);
      }
      if (this.signalrRetryTimer) {
        window.clearInterval(this.signalrRetryTimer);
      }
    });

  }

  initialize(): void {
    if (this.initialized) {
      return;
    }

    this.initialized = true;
    this.startCameraBootstrap();
    this.startSignalrBootstrap();
  }

  selectCamera(cameraId: string): void {
    this.selectedCameraId.set(cameraId);
    this.startTelemetryPolling(cameraId);
    this.startReportPolling(cameraId);
  }

  toggleRequirement(
    camera: CameraViewModel,
    key: keyof CameraRequirements,
    enabled: boolean,
  ): void {
    const payload: CameraRequirements =
      key === 'hardhat'
        ? { ...camera.requirements, hardhat: enabled }
        : key === 'safetyVest'
          ? { ...camera.requirements, safetyVest: enabled }
          : { ...camera.requirements, mask: enabled };

    this.cameraApiService.updateRequirements(camera.cameraId, payload).subscribe((updated) => {
      this.cameras.set(
        this.cameras().map((candidate) =>
          candidate.cameraId === updated.cameraId ? updated : candidate,
        ),
      );
    });
  }

  isCameraActive(cameraId: string): boolean {
    const cam = this.cameras().find(c => c.cameraId === cameraId);
    return cam ? cam.enabled : true;
  }

  toggleCameraActive(cameraId: string): void {
    const cam = this.cameras().find(c => c.cameraId === cameraId);
    if (!cam) return;

    const newStateValue = !cam.enabled;
    
    // .NET araciligiyla hem Python'u hem de .NET registry'sini guncelle
    this.cameraApiService.updateStatus(cameraId, newStateValue).subscribe({
        next: () => {
            // Local state'i de hemen guncelle (optimistic UI)
            this.cameras.update(list => list.map(c => 
                c.cameraId === cameraId ? { ...c, enabled: newStateValue } : c
            ));
            
            // LocalStorage yedegi (istege bagli, artik backend source of truth)
            const saved = localStorage.getItem('camera_status');
            const state = saved ? JSON.parse(saved) : {};
            state[cameraId] = newStateValue;
            localStorage.setItem('camera_status', JSON.stringify(state));
        },
        error: (err) => console.error('Kamera durumu backendde guncellenemedi', err)
    });
  }

  severityClass(severity: TelemetrySeverity): string {
    if (severity === 'critical') {
      return 'severity-critical';
    }
    if (severity === 'warning') {
      return 'severity-warning';
    }
    return '';
  }

  riskClass(level: string): string {
    return `risk-${level.toLowerCase()}`;
  }

  private startTelemetryPolling(cameraId: string): void {
    if (this.telemetryTimer) {
      window.clearInterval(this.telemetryTimer);
    }

    this.loadTelemetry(cameraId);
    this.telemetryTimer = window.setInterval(() => {
      this.loadTelemetry(cameraId);
    }, 4000);
  }

  private loadTelemetry(cameraId: string): void {
    this.cameraApiService.getTelemetry(cameraId).subscribe({
      next: (telemetry) => {
        if (cameraId === this.selectedCameraId()) {
          this.telemetry.set(telemetry);
        }
      },
      error: (error) => {
        console.error('Kamera telemetrisi alınamadı.', error);
      },
    });
  }

  private startReportPolling(cameraId: string): void {
    if (this.reportTimer) {
      window.clearInterval(this.reportTimer);
    }

    this.loadDecisionSupport(cameraId);
    this.reportTimer = window.setInterval(() => {
      this.loadDecisionSupport(cameraId);
    }, 8000);
  }

  private loadDecisionSupport(cameraId: string): void {
    this.decisionSupportApiService.getReport(cameraId).subscribe({
      next: (report) => {
        if (cameraId === this.selectedCameraId()) {
          this.decisionSupport.set(report);
        }
      },
      error: (error) => {
        console.error('Karar destek raporu alınamadı.', error);
      },
    });
  }

  private startCameraBootstrap(): void {
    this.loadCameras();
    this.cameraRetryTimer = window.setInterval(() => {
      if (this.cameras().length === 0) {
        this.loadCameras();
      }
    }, 5000);
  }

  private loadCameras(): void {
    this.cameraApiService
      .getCameras()
      .pipe(
        catchError((error) => {
          console.error('Camera listesi alınamadı.', error);
          this.errorMessage.set(
            '.NET orkestratör API erişilemedi. Kamera sekmeleri yüklenemedi; sistem yeniden deniyor.',
          );
          return of([] as CameraViewModel[]);
        }),
      )
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((cameras) => {
        if (cameras.length === 0) {
          return;
        }

        this.cameras.set(cameras);
        this.errorMessage.set('');

        // İlk yüklemede, tarayıcı hafızasındaki (localStorage) tercihleri backend ile senkronize et
        // (Eger backend'deki durum ile localStorage farkliysa localStorage kazanir — kullanıcı tercihi)
        const saved = localStorage.getItem('camera_status');
        if (saved) {
             const localState = JSON.parse(saved);
             cameras.forEach(c => {
                 const shouldBe = localState[c.cameraId];
                 if (shouldBe !== undefined && shouldBe !== c.enabled) {
                     this.cameraApiService.updateStatus(c.cameraId, shouldBe).subscribe();
                 }
             });
        }

        const selectedCameraId = this.selectedCameraId();
        const nextCameraId =
          cameras.find((camera) => camera.cameraId === selectedCameraId)?.cameraId ??
          cameras[0]?.cameraId ??
          '';

        this.selectedCameraId.set(nextCameraId);

        if (nextCameraId) {
          this.startTelemetryPolling(nextCameraId);
          this.startReportPolling(nextCameraId);
        }

        if (this.cameraRetryTimer) {
          window.clearInterval(this.cameraRetryTimer);
          this.cameraRetryTimer = undefined;
        }
      });
  }

  private startSignalrBootstrap(): void {
    this.tryInitializeSignalr();
    this.signalrRetryTimer = window.setInterval(() => {
      if (!this.signalrInitialized) {
        this.tryInitializeSignalr();
      }
    }, 5000);
  }

  private async tryInitializeSignalr(): Promise<void> {
    if (this.signalrInitialized) {
      return;
    }

    try {
      await this.alertSignalrService.initialize();
      this.signalrInitialized = true;
      this.alertSignalrService.alerts$
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe((alerts) => {
          this.liveAlerts.set(alerts);
        });

      if (this.signalrRetryTimer) {
        window.clearInterval(this.signalrRetryTimer);
        this.signalrRetryTimer = undefined;
      }

      if (this.cameras().length > 0) {
        this.errorMessage.set('');
      }
    } catch (error) {
      console.error('SignalR bağlantısı kurulamadı.', error);
      if (!this.errorMessage()) {
        this.errorMessage.set(
          'SignalR alert bağlantısı kurulamadı; sistem otomatik olarak yeniden deniyor.',
        );
      }
    }
  }
}

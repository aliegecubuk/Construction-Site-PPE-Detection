import { DatePipe, NgClass, NgFor, NgIf } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  effect,
  inject,
  signal,
} from '@angular/core';

import { DecisionSupportReport } from '../../core/models/decision-support.model';
import { DashboardStateService } from '../../core/services/dashboard-state.service';
import { DecisionSupportApiService } from '../../core/services/decision-support-api.service';

@Component({
  selector: 'app-report-page',
  standalone: true,
  imports: [NgIf, NgFor, NgClass, DatePipe],
  template: `
    <section class="page-shell">
      <header class="page-head">
        <div>
          <span class="page-tag">Karar Destek</span>
          <h1>Report</h1>
          <p>Her kamera için ayrı rapor sekmesi. Dashboard seçimi bu sayfayı artık etkilemiyor.</p>
        </div>
        <div class="head-meta">
          <article class="mini-stat">
            <small>Kamera</small>
            <strong>{{ state.cameras().length }}</strong>
          </article>
          <article class="mini-stat">
            <small>Aktif Sekme</small>
            <strong>{{ activeTabLabel() }}</strong>
          </article>
        </div>
      </header>

      <section class="tab-bar" *ngIf="state.cameras().length > 0">
        <button
          *ngFor="let camera of state.cameras(); let i = index"
          type="button"
          class="report-tab"
          [class.active]="camera.cameraId === selectedReportCameraId()"
          (click)="selectReportCamera(camera.cameraId)">
          <span class="report-tab-index">Report {{ i + 1 }}</span>
          <strong>{{ camera.name }}</strong>
        </button>
      </section>

      <section *ngIf="report() as report; else noReport" class="report-layout">
        <article class="content-card overview-card">
          <div class="section-head">
            <div>
              <h2>{{ report.cameraName || activeCameraName() }}</h2>
              <p>{{ report.generatedAt | date: 'dd.MM.yyyy HH:mm:ss' }} · Son {{ report.windowMinutes }} dakika</p>
            </div>
            <span class="risk-pill" [ngClass]="state.riskClass(report.overallRiskLevel)">
              {{ report.overallRiskLevel }}
            </span>
          </div>

          <p class="manager-summary">{{ report.managerSummary }}</p>

          <div class="stats-grid">
            <div class="summary-stat">
              <small>Toplam Alert</small>
              <strong>{{ report.statistics.totalAlerts }}</strong>
            </div>
            <div class="summary-stat">
              <small>KKD Alert</small>
              <strong>{{ report.statistics.ppeAlerts }}</strong>
            </div>
            <div class="summary-stat">
              <small>IoT Alert</small>
              <strong>{{ report.statistics.iotAlerts }}</strong>
            </div>
            <div class="summary-stat">
              <small>Kritik</small>
              <strong>{{ report.statistics.criticalAlerts }}</strong>
            </div>
          </div>
        </article>

        <article class="content-card">
          <div class="section-head slim">
            <h2>Denetim Metni</h2>
          </div>
          <div class="list-grid">
            <div class="text-card" *ngFor="let item of report.inspectionReport">
              <i class="fe fe-check-circle"></i>
              <span>{{ item }}</span>
            </div>
          </div>
        </article>

        <article class="content-card wide">
          <div class="section-head slim">
            <h2>Risk Kategorileri</h2>
          </div>
          <div class="risk-grid">
            <article class="risk-card" *ngFor="let category of report.riskCategories">
              <div class="risk-head">
                <strong>{{ category.categoryName }}</strong>
                <span class="risk-pill" [ngClass]="state.riskClass(category.riskLevel)">
                  {{ category.riskLevel }}
                </span>
              </div>
              <p>{{ category.narrative }}</p>
              <small>{{ category.occurrenceCount }} olay · {{ category.sampleViolations.join(', ') || 'örnek yok' }}</small>
            </article>
          </div>
        </article>

        <article class="content-card">
          <div class="section-head slim">
            <h2>Aksiyon Planı</h2>
          </div>
          <div class="list-grid">
            <div class="text-card" *ngFor="let recommendation of report.preventiveRecommendations">
              <i class="fe fe-arrow-right"></i>
              <span>{{ recommendation }}</span>
            </div>
          </div>
        </article>
      </section>
    </section>

    <ng-template #noReport>
      <section class="empty-state">
        <i class="fe fe-file-text"></i>
        <h2>Report bekleniyor</h2>
        <p>{{ loading() ? 'Seçili sekme için rapor yükleniyor.' : 'Henüz kamera raporu oluşmadı.' }}</p>
      </section>
    </ng-template>
  `,
  styles: [`
    :host {
      display: block;
    }

    .page-shell {
      display: grid;
      gap: 18px;
    }

    .page-head {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      padding: 22px 24px;
      border-radius: 24px;
      background: linear-gradient(135deg, rgba(7, 74, 116, 0.96), rgba(80, 192, 212, 0.88));
      color: #fff;
    }

    .page-tag {
      display: inline-block;
      margin-bottom: 10px;
      padding: 5px 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.14);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .page-head h1 {
      margin: 0;
      font-size: 1.8rem;
    }

    .page-head p {
      margin: 8px 0 0;
      color: rgba(255, 255, 255, 0.84);
    }

    .head-meta {
      display: grid;
      grid-template-columns: repeat(2, minmax(130px, 1fr));
      gap: 12px;
    }

    .mini-stat {
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.12);
      border: 1px solid rgba(255, 255, 255, 0.16);
    }

    .mini-stat small {
      display: block;
      margin-bottom: 8px;
      color: rgba(255, 255, 255, 0.78);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 11px;
    }

    .mini-stat strong {
      font-size: 1rem;
    }

    .tab-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
    }

    .report-tab {
      min-width: 180px;
      border: 0;
      padding: 14px 16px;
      border-radius: 18px;
      background: #fff;
      text-align: left;
      box-shadow: 0 12px 28px rgba(17, 24, 39, 0.08);
      display: grid;
      gap: 4px;
    }

    .report-tab.active {
      background: linear-gradient(135deg, rgba(7, 74, 116, 0.98), rgba(80, 192, 212, 0.92));
      box-shadow: 0 18px 34px rgba(7, 74, 116, 0.18);
    }

    .report-tab-index {
      color: #64748b;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .report-tab strong {
      color: #1b1f3b;
      font-size: 14px;
    }

    .report-tab.active .report-tab-index,
    .report-tab.active strong {
      color: #fff;
    }

    .report-layout {
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
      gap: 18px;
    }

    .content-card {
      padding: 20px;
      border-radius: 22px;
      background: rgba(255, 255, 255, 0.95);
      border: 1px solid rgba(218, 223, 234, 0.9);
      box-shadow: 0 18px 36px rgba(15, 23, 42, 0.08);
    }

    .content-card.wide {
      grid-column: 1 / -1;
    }

    .overview-card {
      grid-column: 1 / -1;
    }

    .section-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      margin-bottom: 14px;
    }

    .section-head.slim {
      margin-bottom: 12px;
    }

    .section-head h2 {
      margin: 0;
      color: #1b1f3b;
      font-size: 1.25rem;
    }

    .section-head p {
      margin: 6px 0 0;
      color: #7e8299;
      font-size: 13px;
    }

    .manager-summary {
      margin: 0 0 16px;
      color: #4b5563;
      line-height: 1.7;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }

    .summary-stat {
      padding: 14px 16px;
      border-radius: 18px;
      background: linear-gradient(180deg, #0f4e75, #0b6d91);
    }

    .summary-stat small {
      display: block;
      margin-bottom: 8px;
      color: rgba(255, 255, 255, 0.78);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 11px;
    }

    .summary-stat strong {
      color: #fff;
      font-size: 1.35rem;
    }

    .list-grid,
    .risk-grid {
      display: grid;
      gap: 12px;
    }

    .text-card,
    .risk-card {
      padding: 14px 16px;
      border-radius: 18px;
      background: #f8fafc;
      border: 1px solid #edf1f7;
    }

    .text-card {
      display: grid;
      grid-template-columns: 24px minmax(0, 1fr);
      gap: 10px;
      align-items: start;
    }

    .text-card i {
      color: #0f4e75;
      line-height: 1.2;
    }

    .text-card span,
    .risk-card p {
      color: #4b5563;
      line-height: 1.6;
    }

    .risk-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 10px;
    }

    .risk-head strong {
      color: #1b1f3b;
      font-size: 15px;
    }

    .risk-pill {
      display: inline-flex;
      align-items: center;
      padding: 7px 12px;
      border-radius: 999px;
      background: #eff3f8;
      color: #1b1f3b;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.07em;
      text-transform: uppercase;
      white-space: nowrap;
    }

    .risk-low {
      background: rgba(34, 197, 94, 0.16);
      color: #166534;
    }

    .risk-medium {
      background: rgba(245, 158, 11, 0.18);
      color: #9a3412;
    }

    .risk-high,
    .risk-critical {
      background: rgba(239, 68, 68, 0.16);
      color: #b91c1c;
    }

    .risk-card small {
      display: block;
      margin-top: 10px;
      color: #7e8299;
    }

    .empty-state {
      display: grid;
      place-items: center;
      gap: 10px;
      min-height: 320px;
      text-align: center;
      padding: 28px;
      border-radius: 24px;
      background: rgba(255, 255, 255, 0.9);
      border: 1px dashed #cbd5e1;
      color: #64748b;
    }

    .empty-state i {
      font-size: 34px;
      color: #0f4e75;
    }

    .empty-state h2,
    .empty-state p {
      margin: 0;
    }

    @media (max-width: 1000px) {
      .page-head,
      .section-head,
      .risk-head {
        flex-direction: column;
        align-items: flex-start;
      }

      .head-meta,
      .report-layout,
      .stats-grid {
        grid-template-columns: 1fr;
      }
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReportPageComponent {
  readonly state = inject(DashboardStateService);
  private readonly decisionSupportApiService = inject(DecisionSupportApiService);

  readonly selectedReportCameraId = signal<string>('');
  readonly loading = signal(false);
  readonly reportCache = signal<Record<string, DecisionSupportReport | undefined>>({});

  readonly report = computed(() => {
    const cameraId = this.selectedReportCameraId();
    return cameraId ? this.reportCache()[cameraId] ?? null : null;
  });

  readonly activeTabLabel = computed(() => {
    const index = this.state.cameras().findIndex(
      (camera) => camera.cameraId === this.selectedReportCameraId(),
    );
    return index >= 0 ? `Report ${index + 1}` : '-';
  });

  readonly activeCameraName = computed(
    () =>
      this.state.cameras().find((camera) => camera.cameraId === this.selectedReportCameraId())?.name ??
      '-',
  );

  constructor() {
    this.state.initialize();

    effect(
      () => {
        const cameras = this.state.cameras();
        if (cameras.length === 0) {
          return;
        }

        const selectedCameraId = this.selectedReportCameraId() || cameras[0].cameraId;
        if (selectedCameraId !== this.selectedReportCameraId()) {
          this.selectedReportCameraId.set(selectedCameraId);
          return;
        }

        if (!this.reportCache()[selectedCameraId]) {
          this.loadReport(selectedCameraId);
        }
      },
      { allowSignalWrites: true },
    );
  }

  selectReportCamera(cameraId: string): void {
    this.selectedReportCameraId.set(cameraId);
    if (!this.reportCache()[cameraId]) {
      this.loadReport(cameraId);
    }
  }

  private loadReport(cameraId: string): void {
    this.loading.set(true);
    this.decisionSupportApiService.getReport(cameraId).subscribe({
      next: (report) => {
        this.reportCache.set({
          ...this.reportCache(),
          [cameraId]: report,
        });
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Kamera bazli report alinamadi.', error);
        this.loading.set(false);
      },
    });
  }
}

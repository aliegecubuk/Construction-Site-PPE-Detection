import { DatePipe, DecimalPipe, NgClass, NgFor, NgIf, UpperCasePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { DashboardStateService } from '../../core/services/dashboard-state.service';

@Component({
  selector: 'app-report-dashboard',
  standalone: true,
  imports: [NgFor, NgIf, NgClass, DatePipe, DecimalPipe, UpperCasePipe, RouterLink],
  template: `
    <section class="dashboard-shell fade-in-up">
      <header class="page-top">
        <h1 class="dashboard-title">Dashboard</h1>
      </header>

      <section class="status-banner" *ngIf="state.errorMessage() as errorMessage">
        <i class="fe fe-alert-triangle"></i>
        <div>
          <strong>Sistem İletişim Uyarısı</strong>
          <p>{{ errorMessage }}</p>
        </div>
      </section>

      <!-- Üst Satır İstatistikler -->
      <section class="stats-grid top-stats">
        
        <article class="surface-card hoverable">
          <div class="card-content-spread">
            <div class="card-left">
              <span class="eyebrow">KAMERA SAYISI</span>
              <strong class="stat-number">{{ state.cameras().length }}</strong>
              <div class="stat-meta text-success">
                <i class="fe fe-check-circle"></i>
                <span>Aktif sistemdeki kameralar</span>
              </div>
            </div>
            <div class="card-right">
              <div class="icon-circle icon-purple"><i class="fe fe-video"></i></div>
            </div>
          </div>
        </article>

        <article class="surface-card hoverable">
          <div class="card-content-spread">
            <div class="card-left">
              <span class="eyebrow">GÜNLÜK İHLALLER</span>
              <strong class="stat-number text-danger">{{ todayAlertsCount() }}</strong>
              <div class="stat-meta text-danger">
                <i class="fe fe-alert-octagon"></i>
                <span>Dikkat Kayıtlı güvenlik ihlali</span>
              </div>
            </div>
            <div class="card-right">
              <div class="icon-circle icon-red"><i class="fe fe-shield-off"></i></div>
            </div>
          </div>
        </article>

        <article class="surface-card hoverable">
          <div class="card-content-spread">
            <div class="card-left">
              <span class="eyebrow">ANALİZ DURUMU</span>
              <strong class="stat-number text-success">{{ activeCamerasCount() }}</strong>
              <div class="stat-meta text-success">
                <i class="fe fe-activity"></i>
                <span>Devam Ediyor Tüm analizler</span>
              </div>
            </div>
            <div class="card-right">
              <div class="icon-circle icon-green"><i class="fe fe-cpu"></i></div>
            </div>
          </div>
        </article>
      </section>

      <!-- Alt Satır: Hızlı Erişim -->
      <h2 class="section-title">HIZLI ERİŞİM</h2>
      <section class="stats-grid bottom-actions">
        
        <article class="surface-card hoverable text-center centered-card">
          <div class="icon-circle icon-blue-light mx-auto"><i class="fe fe-activity"></i></div>
          <h3 class="card-title">İHLAL ALARMLARI</h3>
          <p class="card-desc">Sahadaki son ihlallerin anlık analizi</p>
          <button class="btn-pill btn-dark-blue" routerLink="/uyarilar">İncele →</button>
        </article>

        <article class="surface-card hoverable text-center centered-card">
          <div class="icon-circle icon-blue mx-auto"><i class="fe fe-map"></i></div>
          <h3 class="card-title">KAMERA YÖNETİMİ</h3>
          <p class="card-desc">Saha izleme noktaları ve kural denetimi</p>
          <button class="btn-pill btn-blue" routerLink="/kameralar">Listele →</button>
        </article>

        <article class="surface-card hoverable text-center centered-card">
          <div class="icon-circle icon-yellow mx-auto"><i class="fe fe-pie-chart"></i></div>
          <h3 class="card-title">HAFTALIK RAPOR</h3>
          <p class="card-desc">Saha durumunun genel analiz raporlaması</p>
          <button class="btn-pill btn-yellow" routerLink="/report">İncele →</button>
        </article>

      </section>
    </section>
  `,
  styles: [`
    :host { display: block; }

    .dashboard-shell {
      display: grid;
      gap: 20px;
      color: #334155;
    }

    .fade-in-up {
      animation: fadeInUp 0.4s ease-out forwards;
      opacity: 0;
      transform: translateY(10px);
    }
    @keyframes fadeInUp { to { opacity: 1; transform: translateY(0); } }

    .page-top {
      margin-bottom: 4px;
    }

    .dashboard-title {
      margin: 0;
      font-size: 1.4rem;
      font-weight: 700;
      color: #0f172a;
    }

    .section-title {
      font-size: 0.85rem;
      font-weight: 700;
      color: #64748b;
      margin: 12px 0 0;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 24px;
    }

    .surface-card {
      background: #ffffff;
      border-radius: 20px;
      padding: 24px 28px;
      border: 1px solid rgba(226, 232, 240, 0.8);
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.02);
      transition: all 0.2s ease;
    }

    .surface-card.hoverable:hover {
      transform: translateY(-4px);
      box-shadow: 0 16px 40px rgba(15, 23, 42, 0.06);
    }

    .card-content-spread {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }

    .card-left {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .eyebrow {
      font-size: 0.75rem;
      font-weight: 700;
      color: #64748b;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .stat-number {
      font-size: 2.2rem;
      font-weight: 600;
      color: #1e293b;
      line-height: 1.1;
      margin-top: 2px;
    }

    .stat-meta {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 0.85rem;
      font-weight: 500;
      color: #64748b;
      margin-top: 8px;
    }

    .stat-meta i { font-size: 1.1rem; }

    .text-success { color: #10b981; }
    .text-danger { color: #ef4444; }

    .icon-circle {
      width: 52px;
      height: 52px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      font-size: 1.4rem;
    }

    .icon-purple { background: #f3e8ff; color: #a855f7; }
    .icon-red { background: #fee2e2; color: #ef4444; }
    .icon-green { background: #d1fae5; color: #10b981; }
    
    .icon-blue-light { background: #e0f2fe; color: #38bdf8; }
    .icon-blue { background: #dbeafe; color: #3b82f6; }
    .icon-yellow { background: #fef9c3; color: #eab308; }

    .text-center { text-align: center; }
    .mx-auto { margin-inline: auto; }
    .centered-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 36px 24px;
      gap: 12px;
    }

    .card-title {
      margin: 12px 0 0;
      font-size: 0.95rem;
      font-weight: 700;
      color: #475569;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .card-desc {
      margin: 0 0 16px;
      font-size: 0.9rem;
      color: #94a3b8;
    }

    .btn-pill {
      padding: 8px 24px;
      border-radius: 999px;
      border: none;
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.2s;
    }

    .btn-dark-blue { background: #1e3a8a; color: #fff; }
    .btn-dark-blue:hover { background: #172554; }

    .btn-blue { background: #3b82f6; color: #fff; }
    .btn-blue:hover { background: #2563eb; }

    .btn-yellow { background: #eab308; color: #fff; }
    .btn-yellow:hover { background: #ca8a04; }

    .status-banner {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px 20px;
      border-radius: 20px;
      background: #fdf2f2;
      border: 1px solid #fecdd3;
      color: #be123c;
    }
    .status-banner p { margin: 4px 0 0; }

    @media (max-width: 1200px) {
      .stats-grid { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 768px) {
      .stats-grid { grid-template-columns: 1fr; }
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReportDashboardComponent {
  readonly state = inject(DashboardStateService);

  readonly activeCamerasCount = this.state.activeCamerasCount;
  readonly todayAlertsCount = computed(() => {
    // Toplam ihlal sayısını basitçe simüle edebilir ya da liveAlerts length alabiliriz.
    // Eger 0 ise yine iyi. Backend siniri var.
    return this.state.liveAlerts().length || 0;
  });

  constructor() {
    this.state.initialize();
  }

  humanizeRisk(level: string): string {
    const l = (level || '').toLowerCase();
    if (l === 'critical') return 'Kritik';
    if (l === 'high') return 'Yüksek';
    if (l === 'medium') return 'Orta';
    if (l === 'low') return 'Düşük';
    return level;
  }
}

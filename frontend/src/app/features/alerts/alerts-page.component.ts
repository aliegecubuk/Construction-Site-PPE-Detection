import { DatePipe, NgFor, NgIf, NgClass } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';

import { ViolationAlert } from '../../core/models/alert.model';
import { DashboardStateService } from '../../core/services/dashboard-state.service';

@Component({
  selector: 'app-alerts-page',
  standalone: true,
  imports: [NgFor, NgIf, NgClass, DatePipe],
  template: `
    <section class="page-shell">
      <header class="page-head fade-in-up">
        <div>
          <span class="page-tag">Gerçek Zamanlı</span>
          <h1>Son İhlaller ve Alarmlar</h1>
          <p>Yapay zeka analiz motoru tarafından raporlanan güvenlik ihlalleri.</p>
        </div>
        <div class="page-stats">
          <article class="mini-stat">
            <small>Filtrelenmiş Kayıt</small>
            <strong>{{ filteredAlerts().length }}</strong>
          </article>
        </div>
      </header>

      <section class="filter-card fade-in-up" style="animation-delay: 0.1s;">
        <div class="filter-grid">
          <label class="filter-field">
            <span>Kamera</span>
            <select [value]="selectedCameraFilter()" (change)="updateCameraFilter($any($event.target).value)">
              <option value="">Tüm Kameralar</option>
              <option *ngFor="let camera of state.cameras()" [value]="camera.cameraId">
                {{ camera.name }}
              </option>
            </select>
          </label>

          <label class="filter-field">
            <span>Uyarı Türü</span>
            <select [value]="selectedViolationType()" (change)="updateViolationType($any($event.target).value)">
              <option value="">Tüm Türler</option>
              <option *ngFor="let violationType of violationTypes()" [value]="violationType">
                {{ violationType }}
              </option>
            </select>
          </label>

          <label class="filter-field">
            <span>Başlangıç</span>
            <input type="date" [value]="dateFrom()" (change)="updateDateFrom($any($event.target).value)">
          </label>

          <label class="filter-field">
            <span>Bitiş</span>
            <input type="date" [value]="dateTo()" (change)="updateDateTo($any($event.target).value)">
          </label>

          <button type="button" class="reset-button ripple" (click)="resetFilters()">
             Filtreleri Temizle
          </button>
        </div>
      </section>

      <section class="status-banner" *ngIf="state.errorMessage() as errorMessage">
        <strong>Sistem Uyarısı</strong>
        <p>{{ errorMessage }}</p>
      </section>

      <section class="alerts-list fade-in-up" style="animation-delay: 0.2s;" *ngIf="filteredAlerts().length > 0; else emptyAlerts">
        <article class="list-item" *ngFor="let alert of filteredAlerts()">
          
          <div class="list-info">
            <span class="badge" [ngClass]="getBadgeClass(alert.violationType)">
              {{ alert.violationType }}
            </span>
            <span class="item-title">{{ alert.message || 'Kural İhlali Tespit Edildi' }}</span>
            <span class="item-meta"><i class="fe fe-video"></i> {{ alert.cameraName }}</span>
            <span class="item-meta"><i class="fe fe-clock"></i> {{ alert.occurredAt | date: 'dd.MM.yyyy HH:mm:ss' }}</span>
          </div>

          <div class="mini-frame" (click)="openImageModal(alert)">
             <img [src]="'http://localhost:8000/api/v1/alerts/' + alert.eventId + '/frame'" 
                  onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'"
                  [alt]="alert.violationType" class="mini-img" loading="lazy" />
             <!-- Fallback (Resim yoksa) -->
             <div class="mini-placeholder" style="display: none;">
               <i class="fe fe-image"></i>
             </div>
             <div class="zoom-hover">
               <i class="fe fe-maximize-2"></i>
             </div>
          </div>

        </article>
      </section>
      
      <!-- Fullscreen Image Modal -->
      <div class="modal-backdrop" *ngIf="zoomedAlert()" (click)="closeModal()">
        <div class="modal-panel slide-up" (click)="$event.stopPropagation()">
           <button class="btn-close-abs" (click)="closeModal()"><i class="fe fe-x"></i></button>
           <div class="zoomed-image-wrapper">
             <img [src]="'http://localhost:8000/api/v1/alerts/' + zoomedAlert()?.eventId + '/frame'" 
                  onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'"
                  alt="Büyütülmüş Çerçeve"/>
             <!-- Fallback Modal -->
             <div class="placeholder-frame-modal" style="display: none;">
               <i class="fe fe-image"></i>
               <p>Frame kaydı mevcut değil.</p>
             </div>
           </div>
           <div class="modal-info">
             <h3>{{ zoomedAlert()?.cameraName }}</h3>
             <p>{{ zoomedAlert()?.occurredAt | date: 'HH:mm:ss dd.MM.yyyy' }} - <strong>{{ zoomedAlert()?.violationType }}</strong></p>
           </div>
        </div>
      </div>
    </section>

    <ng-template #emptyAlerts>
      <section class="empty-state">
        <div class="empty-icon"><i class="fe fe-shield-off"></i></div>
        <h2>İhlal Kaydı Bulunmuyor</h2>
        <p>Seçili kriterlere uygun herhangi bir güvenlik ihlali veya alarm tespit edilmedi.</p>
        <button class="btn-outline" (click)="resetFilters()">Tüm İhlalleri Göster</button>
      </section>
    </ng-template>
  `,
  styles: [`
    :host { display: block; }

    .page-shell {
      display: grid;
      gap: 24px;
      color: #0f172a;
    }

    .fade-in-up {
      animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      opacity: 0;
      transform: translateY(15px);
    }
    @keyframes fadeInUp {
      to { opacity: 1; transform: translateY(0); }
    }

    .page-head {
      display: flex;
      justify-content: space-between;
      gap: 20px;
      align-items: center;
      padding: 28px 32px;
      border-radius: 24px;
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.8));
      backdrop-filter: blur(20px);
      box-shadow: 0 10px 40px rgba(15, 23, 42, 0.04);
      border: 1px solid rgba(226, 232, 240, 0.8);
    }

    .page-tag {
      display: inline-block;
      margin-bottom: 8px;
      padding: 5px 12px;
      border-radius: 999px;
      background: rgba(225, 29, 72, 0.1);
      color: #e11d48;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .page-head h1 { margin: 0; font-size: 2rem; font-weight: 800; letter-spacing: -0.02em; }
    .page-head p { margin: 6px 0 0; color: #64748b; font-size: 0.95rem; }

    .mini-stat {
      padding: 16px 24px;
      border-radius: 18px;
      background: rgba(241, 245, 249, 0.8);
      border: 1px solid rgba(226, 232, 240, 0.9);
      text-align: right;
    }

    .mini-stat small {
      display: block; margin-bottom: 4px; font-size: 0.8rem;
      font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b;
    }
    .mini-stat strong { font-size: 1.5rem; color: #0f172a; font-weight: 800; }

    .filter-card {
      padding: 24px;
      border-radius: 24px;
      background: #ffffff;
      border: 1px solid rgba(226, 232, 240, 0.8);
      box-shadow: 0 14px 40px rgba(15, 23, 42, 0.03);
    }

    .filter-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      align-items: end;
    }

    .filter-field { display: grid; gap: 8px; }
    .filter-field span {
      font-size: 0.8rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;
    }
    .filter-field select, .filter-field input {
      width: 100%; border: 2px solid #e2e8f0; border-radius: 12px; padding: 12px 14px;
      background: #f8fafc; font-size: 0.95rem; transition: all 0.2s;
    }
    .filter-field select:focus, .filter-field input:focus {
      outline: none; border-color: #38bdf8; background: #fff;
    }

    .reset-button {
      padding: 14px 20px; height: 46px; border-radius: 12px; border: none; font-weight: 700;
      background: #f1f5f9; color: #334155; cursor: pointer; transition: all 0.2s ease;
    }
    .reset-button:hover { background: #e2e8f0; color: #0f172a; }

    .alerts-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .list-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #fff;
      border-radius: 12px;
      padding: 12px 20px;
      border: 1px solid rgba(226, 232, 240, 0.8);
      box-shadow: 0 4px 10px rgba(0,0,0,0.02);
      transition: all 0.2s;
    }
    .list-item:hover { box-shadow: 0 8px 20px rgba(0,0,0,0.05); }

    .list-info {
      display: flex;
      align-items: center;
      gap: 20px;
      flex-wrap: wrap;
    }

    .item-title {
      font-size: 0.95rem;
      font-weight: 600;
      color: #0f172a;
    }

    .item-meta {
      font-size: 0.85rem;
      color: #64748b;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .item-meta i { font-size: 1rem; }

    .mini-frame {
      position: relative;
      width: 60px;
      height: 60px;
      border-radius: 8px;
      overflow: hidden;
      background: #f1f5f9;
      cursor: zoom-in;
      flex-shrink: 0;
      border: 1px solid #e2e8f0;
    }

    .mini-img {
      width: 100%; height: 100%; object-fit: cover;
      transition: transform 0.3s;
    }
    .mini-frame:hover .mini-img { transform: scale(1.1); }

    .mini-placeholder {
      width: 100%; height: 100%;
      display: flex; justify-content: center; align-items: center;
      background: #f8fafc;
      color: #94a3b8;
      font-size: 1.5rem;
    }

    .zoom-hover {
      position: absolute; inset: 0; background: rgba(0,0,0,0.3);
      display: grid; place-items: center; opacity: 0; transition: opacity 0.2s;
      color: white; font-size: 1.2rem;
    }
    .mini-frame:hover .zoom-hover { opacity: 1; }

    .badge {
      display: inline-flex; align-items: center; padding: 6px 14px;
      border-radius: 8px; font-size: 0.75rem; font-weight: 800;
      text-transform: uppercase; letter-spacing: 0.05em;
    }
    .badge-red { background: #ffe4e6; color: #e11d48; border: 1px solid #fecdd3; }
    .badge-orange { background: #ffedd5; color: #ea580c; border: 1px solid #fed7aa; }
    .badge-yellow { background: #fef9c3; color: #ca8a04; border: 1px solid #fef08a; }
    .badge-default { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }

    /* Empty state */
    .empty-state {
      display: grid; place-items: center; text-align: center; padding: 60px 20px;
      background: #fff; border-radius: 24px; border: 1px dashed #cbd5e1;
    }
    .empty-icon { width: 64px; height: 64px; border-radius: 20px; background: #f1f5f9; color: #94a3b8; font-size: 32px; display: grid; place-items: center; margin-bottom: 16px; }
    .empty-state h2 { margin: 0 0 8px; color: #0f172a; }
    .empty-state p { color: #64748b; max-width: 400px; margin: 0 0 20px; line-height: 1.6; }
    .btn-outline { padding: 12px 24px; border-radius: 12px; border: 2px solid #e2e8f0; background: transparent; color: #475569; font-weight: 600; cursor: pointer; transition: all 0.2s; }
    .btn-outline:hover { border-color: #cbd5e1; background: #f8fafc; }

    /* Fullscreen Modal */
    .modal-backdrop {
      position: fixed; inset: 0; z-index: 9999;
      background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(12px);
      display: grid; place-items: center; padding: 20px;
    }
    .modal-panel {
      position: relative; max-width: 1200px; width: 100%;
      background: #000; border-radius: 16px; overflow: hidden;
      box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
    }
    .btn-close-abs {
      position: absolute; top: 16px; right: 16px; z-index: 10;
      width: 40px; height: 40px; border-radius: 12px; background: rgba(0,0,0,0.5); color: #fff;
      border: none; font-size: 1.4rem; cursor: pointer; transition: background 0.2s;
    }
    .btn-close-abs:hover { background: #e11d48; }
    
    .zoomed-image-wrapper { width: 100%; display: grid; place-items: center; }
    .zoomed-image-wrapper img { width: 100%; max-height: 80vh; object-fit: contain; }
    
    .modal-info { padding: 20px 24px; background: #1e293b; color: #fff; }
    .modal-info h3 { margin: 0 0 4px; font-size: 1.25rem; }
    .modal-info p { margin: 0; color: #94a3b8; font-size: 0.95rem; }
    
    .slide-up { animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
    @keyframes slideUp { from { opacity: 0; transform: translateY(30px) scale(0.95); } to { opacity: 1; transform: translateY(0) scale(1); } }

  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AlertsPageComponent {
  readonly state = inject(DashboardStateService);

  readonly selectedCameraFilter = signal('');
  readonly selectedViolationType = signal('');
  readonly dateFrom = signal('');
  readonly dateTo = signal('');
  
  readonly zoomedAlert = signal<ViolationAlert | null>(null);

  readonly violationTypes = computed(() =>
    Array.from(new Set(this.state.liveAlerts().map((alert) => alert.violationType))).sort(),
  );

  readonly filteredAlerts = computed(() => {
    const cameraFilter = this.selectedCameraFilter();
    const violationType = this.selectedViolationType();
    const dateFrom = this.dateFrom();
    const dateTo = this.dateTo();

    return [...this.state.liveAlerts()]
      .filter((alert) => this.matchesFilters(alert, cameraFilter, violationType, dateFrom, dateTo))
      .sort((left, right) => new Date(right.occurredAt).getTime() - new Date(left.occurredAt).getTime());
  });

  constructor() {
    this.state.initialize();
    
    // Filtre ayarlarini localStorage'dan yükle
    const savedCam = localStorage.getItem('alert_filter_cam');
    if (savedCam) this.selectedCameraFilter.set(savedCam);
    
    const savedType = localStorage.getItem('alert_filter_type');
    if (savedType) this.selectedViolationType.set(savedType);

    const savedFrom = localStorage.getItem('alert_filter_from');
    if (savedFrom) this.dateFrom.set(savedFrom);

    const savedTo = localStorage.getItem('alert_filter_to');
    if (savedTo) this.dateTo.set(savedTo);
  }

  // Filtreleri güncelleyince localStorage'a da kaydetmek için metotlar:
  updateCameraFilter(val: string) {
    this.selectedCameraFilter.set(val);
    localStorage.setItem('alert_filter_cam', val);
  }

  updateViolationType(val: string) {
    this.selectedViolationType.set(val);
    localStorage.setItem('alert_filter_type', val);
  }

  updateDateFrom(val: string) {
    this.dateFrom.set(val);
    localStorage.setItem('alert_filter_from', val);
  }

  updateDateTo(val: string) {
    this.dateTo.set(val);
    localStorage.setItem('alert_filter_to', val);
  }

  resetFilters(): void {
    this.selectedCameraFilter.set('');
    this.selectedViolationType.set('');
    this.dateFrom.set('');
    this.dateTo.set('');
    localStorage.removeItem('alert_filter_cam');
    localStorage.removeItem('alert_filter_type');
    localStorage.removeItem('alert_filter_from');
    localStorage.removeItem('alert_filter_to');
  }

  openImageModal(alert: ViolationAlert): void {
    this.zoomedAlert.set(alert);
  }

  closeModal(): void {
    this.zoomedAlert.set(null);
  }

  getBadgeClass(violationType: string): string {
    const type = violationType?.toLowerCase() || '';
    if (type.includes('baret') || type.includes('maske') || type.includes('yok')) return 'badge-red';
    if (type.includes('yelek') || type.includes('tehlike')) return 'badge-orange';
    if (type.includes('ihlal')) return 'badge-yellow';
    return 'badge-default';
  }

  private matchesFilters(
    alert: ViolationAlert,
    cameraFilter: string,
    violationType: string,
    dateFrom: string,
    dateTo: string,
  ): boolean {
    const occurredAt = new Date(alert.occurredAt).getTime();
    const fromTime = dateFrom ? new Date(`${dateFrom}T00:00:00`).getTime() : Number.NEGATIVE_INFINITY;
    const toTime = dateTo ? new Date(`${dateTo}T23:59:59`).getTime() : Number.POSITIVE_INFINITY;

    return (
      (!cameraFilter || alert.cameraId === cameraFilter) &&
      (!violationType || alert.violationType === violationType) &&
      occurredAt >= fromTime &&
      occurredAt <= toTime
    );
  }
}

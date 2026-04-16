import { NgClass, NgFor, NgIf } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject, signal, computed } from '@angular/core';

import { CameraViewModel, CameraRequirements } from '../../core/models/camera.model';
import { DashboardStateService } from '../../core/services/dashboard-state.service';
import { CameraApiService } from '../../core/services/camera-api.service';

@Component({
  selector: 'app-camera-management',
  standalone: true,
  imports: [NgIf, NgFor, NgClass],
  template: `
    <section class="page-shell">
      <header class="page-head fade-in-up">
        <div>
          <span class="page-tag">Konfigürasyon</span>
          <h1>Kamera Yönetimi</h1>
          <p>Saha izleme noktalarını ve donanım denetim kurallarını yapılandırın.</p>
        </div>
        <button class="btn-primary ripple" (click)="openAddModal()">
          <i class="fe fe-plus"></i>
          Yeni Kamera Ekle
        </button>
      </header>

      <section class="content-card table-wrapper fade-in-up" style="animation-delay: 0.1s;">
        <table class="modern-table">
          <thead>
            <tr>
              <th>Kamera Adı</th>
              <th>RTSP URL</th>
              <th class="text-center">Analiz Durumu</th>
              <th class="text-center">Durum</th>
              <th class="text-right">İşlemler</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let camera of state.cameras(); let i = index" class="row-entry">
              <td>
                <div class="camera-name">
                  <div class="camera-icon" [ngClass]="{'passive-icon': !state.isCameraActive(camera.cameraId)}"><i class="fe fe-video"></i></div>
                  <strong>{{ camera.name }}</strong>
                </div>
              </td>
              <td><span class="url-badge">{{ camera.streamUrl }}</span></td>
              <td class="text-center">
                <label class="toggle-switch">
                  <input type="checkbox" [checked]="state.isCameraActive(camera.cameraId)" (change)="state.toggleCameraActive(camera.cameraId)">
                  <span class="slider round"></span>
                </label>
              </td>
              <td class="text-center">
                <span class="status-badge" [ngClass]="state.isCameraActive(camera.cameraId) ? 'active' : 'passive'">
                  {{ state.isCameraActive(camera.cameraId) ? 'Aktif' : 'Pasif' }}
                </span>
              </td>
              <td class="text-right">
                <div class="action-btns">
                  <button class="btn-icon edit" (click)="openEditModal(camera)" title="Düzenle"><i class="fe fe-edit-2"></i></button>
                  <button class="btn-icon delete" title="Sil"><i class="fe fe-trash-2"></i></button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Kamera Ekle / Düzenle Modalı -->
      <div class="modal-backdrop" *ngIf="isModalOpen()" (click)="closeModal()">
        <div class="modal-panel slide-up" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h2>{{ editingCamera() ? 'Kamera Düzenle' : 'Yeni Kamera Ekle' }}</h2>
            <button class="btn-close" (click)="closeModal()"><i class="fe fe-x"></i></button>
          </div>
          
          <div class="modal-body">
            <div class="form-group">
              <label>Kamera Adı</label>
              <input type="text" placeholder="Örn: 1. Kat Girişi" [value]="editingCamera()?.name || ''" class="modern-input">
            </div>
            <div class="form-group">
              <label>RTSP URL / Bağlantı Adresi</label>
              <input type="text" placeholder="rtsp://..." [value]="editingCamera()?.streamUrl || ''" class="modern-input">
            </div>
            
            <div class="rules-section">
              <h3>Kurallar (Zorunlu İSG Donanımları)</h3>
              <p>Bu kamerada ihlal olarak algılanacak kuralları seçin.</p>
              
              <div class="checkbox-grid">
                <label class="modern-checkbox">
                  <input type="checkbox" [checked]="editingCamera()?.requirements?.mask || false"
                         (change)="toggleRule('mask', $any($event.target).checked)">
                  <span class="box"></span>
                  <span class="label-text">Maske Kontrolü</span>
                </label>
                <label class="modern-checkbox">
                  <input type="checkbox" [checked]="editingCamera()?.requirements?.safetyVest || false"
                         (change)="toggleRule('safetyVest', $any($event.target).checked)">
                  <span class="box"></span>
                  <span class="label-text">Yelek Kontrolü</span>
                </label>
                <label class="modern-checkbox">
                  <input type="checkbox" [checked]="editingCamera()?.requirements?.hardhat || false"
                         (change)="toggleRule('hardhat', $any($event.target).checked)">
                  <span class="box"></span>
                  <span class="label-text">Baret Kontrolü</span>
                </label>
              </div>
            </div>
          </div>
          
          <div class="modal-footer">
            <button class="btn-ghost" (click)="closeModal()">İptal</button>
            <button class="btn-primary" (click)="closeModal()">Kaydet</button>
          </div>
        </div>
      </div>
    </section>
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
      background: rgba(14, 165, 233, 0.1);
      color: #0284c7;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .page-head h1 {
      margin: 0;
      font-size: 2rem;
      font-weight: 800;
      letter-spacing: -0.02em;
    }

    .page-head p {
      margin: 6px 0 0;
      color: #64748b;
      font-size: 0.95rem;
    }

    .btn-primary {
      padding: 12px 24px;
      border-radius: 14px;
      background: linear-gradient(135deg, #0284c7, #0369a1);
      color: #fff;
      border: none;
      font-weight: 600;
      font-size: 0.95rem;
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      box-shadow: 0 8px 20px rgba(2, 132, 199, 0.3);
      transition: all 0.3s ease;
    }

    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 25px rgba(2, 132, 199, 0.4);
    }

    .content-card {
      padding: 24px;
      border-radius: 24px;
      background: #ffffff;
      border: 1px solid rgba(226, 232, 240, 0.8);
      box-shadow: 0 14px 40px rgba(15, 23, 42, 0.05);
      overflow-x: auto;
    }

    .modern-table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
    }

    .modern-table th {
      padding: 16px;
      color: #64748b;
      font-size: 0.85rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      text-align: left;
      border-bottom: 2px solid #f1f5f9;
    }

    .modern-table td {
      padding: 18px 16px;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: middle;
    }

    .row-entry {
      transition: all 0.2s ease;
    }

    .row-entry:hover {
      background: #f8fafc;
      transform: scale(1.002);
    }

    .text-center { text-align: center !important; }
    .text-right { text-align: right !important; }

    .camera-name {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .camera-icon {
      width: 40px;
      height: 40px;
      border-radius: 12px;
      background: #f0f9ff;
      color: #0284c7;
      display: grid;
      place-items: center;
      font-size: 18px;
    }

    .camera-name strong {
      font-size: 1rem;
      color: #0f172a;
    }

    .url-badge {
      padding: 6px 12px;
      border-radius: 8px;
      background: #f1f5f9;
      color: #475569;
      font-family: monospace;
      font-size: 0.85rem;
    }

    .status-badge {
      display: inline-flex;
      align-items: center;
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 0.8rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .status-badge.active {
      background: rgba(16, 185, 129, 0.15);
      color: #059669;
    }

    .status-badge.passive {
      background: rgba(226, 232, 240, 0.4);
      color: #64748b;
    }
    
    .passive-icon {
      background: #f1f5f9;
      color: #94a3b8;
    }

    .action-btns {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
    }

    .btn-icon {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      border: none;
      display: grid;
      place-items: center;
      cursor: pointer;
      transition: all 0.2s ease;
      background: #f1f5f9;
      color: #64748b;
    }

    .btn-icon.edit:hover { background: #e0f2fe; color: #0284c7; }
    .btn-icon.delete:hover { background: #fee2e2; color: #ef4444; }

    /* Toggle Switch */
    .toggle-switch {
      position: relative;
      display: inline-block;
      width: 44px;
      height: 24px;
    }
    .toggle-switch input { opacity: 0; width: 0; height: 0; }
    .slider {
      position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
      background-color: #cbd5e1; transition: .3s; border-radius: 34px;
    }
    .slider:before {
      position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px;
      background-color: white; transition: .3s; border-radius: 50%;
    }
    input:checked + .slider { background-color: #0284c7; }
    input:checked + .slider:before { transform: translateX(20px); }

    /* Modal Styles */
    .modal-backdrop {
      position: fixed;
      inset: 0;
      z-index: 1000;
      background: rgba(15, 23, 42, 0.4);
      backdrop-filter: blur(8px);
      display: grid;
      place-items: center;
      padding: 20px;
    }

    .modal-panel {
      width: 100%;
      max-width: 520px;
      background: #fff;
      border-radius: 24px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
      border: 1px solid rgba(226, 232, 240, 0.8);
      overflow: hidden;
    }

    .slide-up {
      animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    @keyframes slideUp {
      from { opacity: 0; transform: translateY(40px) scale(0.95); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    .modal-header {
      padding: 24px;
      border-bottom: 1px solid #f1f5f9;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .modal-header h2 {
      margin: 0;
      font-size: 1.25rem;
      font-weight: 700;
    }

    .btn-close {
      background: none;
      border: none;
      font-size: 1.2rem;
      color: #64748b;
      cursor: pointer;
      width: 32px;
      height: 32px;
      border-radius: 8px;
    }

    .btn-close:hover { background: #f1f5f9; color: #0f172a; }

    .modal-body {
      padding: 24px;
      display: grid;
      gap: 20px;
    }

    .form-group { display: grid; gap: 8px; }
    .form-group label {
      font-size: 0.85rem;
      font-weight: 600;
      color: #475569;
    }

    .modern-input {
      width: 100%;
      padding: 14px 16px;
      border-radius: 12px;
      border: 2px solid #e2e8f0;
      background: #f8fafc;
      font-size: 0.95rem;
      transition: all 0.2s;
    }

    .modern-input:focus {
      outline: none;
      border-color: #38bdf8;
      background: #fff;
      box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.1);
    }

    .rules-section {
      margin-top: 10px;
      padding: 20px;
      background: #f8fafc;
      border-radius: 16px;
      border: 1px solid #e2e8f0;
    }

    .rules-section h3 { margin: 0; font-size: 0.95rem; font-weight: 700; }
    .rules-section p { margin: 4px 0 16px; font-size: 0.85rem; color: #64748b; }

    .checkbox-grid {
      display: grid;
      gap: 12px;
    }

    .modern-checkbox {
      display: flex;
      align-items: center;
      gap: 12px;
      cursor: pointer;
      padding: 12px;
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      transition: all 0.2s;
    }

    .modern-checkbox:hover { border-color: #bae6fd; }

    .modern-checkbox input { display: none; }
    
    .modern-checkbox .box {
      width: 22px;
      height: 22px;
      border: 2px solid #cbd5e1;
      border-radius: 6px;
      display: grid;
      place-items: center;
      transition: all 0.2s;
    }

    .modern-checkbox input:checked + .box {
      background: #0284c7;
      border-color: #0284c7;
    }
    
    .modern-checkbox input:checked + .box::after {
      content: "✓";
      color: white;
      font-size: 14px;
      font-weight: bold;
    }

    .modern-checkbox .label-text {
      font-size: 0.95rem;
      font-weight: 600;
      color: #334155;
    }

    .modal-footer {
      padding: 24px;
      border-top: 1px solid #f1f5f9;
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      background: #f8fafc;
    }

    .btn-ghost {
      padding: 12px 24px;
      border-radius: 14px;
      background: transparent;
      color: #64748b;
      border: none;
      font-weight: 600;
      cursor: pointer;
    }

    .btn-ghost:hover { background: #e2e8f0; color: #0f172a; }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CameraManagementComponent {
  readonly state = inject(DashboardStateService);
  private cameraApiService = inject(CameraApiService);

  readonly isModalOpen = signal(false);
  readonly editingCamera = signal<CameraViewModel | null>(null);

  constructor() {
    this.state.initialize();
  }

  toggleRule(ruleKey: 'mask' | 'safetyVest' | 'hardhat', checked: boolean) {
    const cam = this.editingCamera();
    if (cam) {
      // Backend apiyi cagirip degisikligi kaydetmek icin state servisteki hazir metodu kullan
      this.state.toggleRequirement(cam, ruleKey, checked);
      // Yerel UI degisikligini de uygula ki modal tiklandiginda tepki versin
      this.editingCamera.set({
        ...cam,
        requirements: { ...cam.requirements, [ruleKey]: checked }
      });
    }
  }

  openAddModal() {
    this.editingCamera.set(null);
    this.isModalOpen.set(true);
  }

  openEditModal(camera: CameraViewModel) {
    this.editingCamera.set(camera);
    this.isModalOpen.set(true);
  }

  closeModal() {
    this.isModalOpen.set(false);
    this.editingCamera.set(null);
  }
}

import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="app-shell">
      <header class="topbar">
        <div class="brand-block">
          <img src="assets/images/brand/logo.png" alt="REPORT-AI logo">
          <div>
            <strong>REPORT-AI</strong>
            <span>Construction Site Safety Hub</span>
          </div>
        </div>

        <nav class="topnav">
          <a routerLink="/" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: true }">Dashboard</a>
          <a routerLink="/uyarilar" routerLinkActive="active">Uyarılar</a>
          <a routerLink="/kameralar" routerLinkActive="active">Kamera Yönetimi</a>
          <a routerLink="/report" routerLinkActive="active">Report</a>
        </nav>
      </header>

      <main class="page-frame">
        <router-outlet />
      </main>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      min-height: 100vh;
      background:
        radial-gradient(circle at top left, rgba(80, 192, 212, 0.18), transparent 24%),
        linear-gradient(180deg, #f4f8fc 0%, #edf3f9 100%);
    }

    .app-shell {
      max-width: 1560px;
      margin: 0 auto;
      padding: 18px 22px 28px;
    }

    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      margin-bottom: 18px;
      padding: 14px 18px;
      border-radius: 24px;
      background: rgba(255, 255, 255, 0.82);
      border: 1px solid rgba(218, 223, 234, 0.9);
      box-shadow: 0 18px 36px rgba(15, 23, 42, 0.08);
      backdrop-filter: blur(14px);
    }

    .brand-block {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }

    .brand-block img {
      width: 40px;
      height: 40px;
      object-fit: contain;
      border-radius: 12px;
      background: linear-gradient(135deg, rgba(7, 74, 116, 0.95), rgba(80, 192, 212, 0.9));
      padding: 7px;
    }

    .brand-block strong,
    .brand-block span {
      display: block;
    }

    .brand-block strong {
      color: #0f4e75;
      font-size: 0.95rem;
      letter-spacing: 0.06em;
    }

    .brand-block span {
      color: #64748b;
      font-size: 0.92rem;
    }

    .topnav {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .topnav a {
      padding: 10px 14px;
      border-radius: 999px;
      color: #475569;
      font-weight: 700;
      text-decoration: none;
      transition: background 0.18s ease, color 0.18s ease;
    }

    .topnav a.active {
      background: linear-gradient(135deg, rgba(7, 74, 116, 0.98), rgba(80, 192, 212, 0.92));
      color: #fff;
      box-shadow: 0 12px 28px rgba(7, 74, 116, 0.22);
    }

    .page-frame {
      min-height: calc(100vh - 120px);
    }

    @media (max-width: 900px) {
      .app-shell {
        padding: 14px 14px 24px;
      }

      .topbar {
        flex-direction: column;
        align-items: flex-start;
      }
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent {}

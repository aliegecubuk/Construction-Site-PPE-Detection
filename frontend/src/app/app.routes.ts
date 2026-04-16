import { Routes } from '@angular/router';

import { AlertsPageComponent } from './features/alerts/alerts-page.component';
import { CameraManagementComponent } from './features/cameras/camera-management.component';
import { ReportDashboardComponent } from './features/dashboard/report-dashboard.component';
import { ReportPageComponent } from './features/report/report-page.component';

export const appRoutes: Routes = [
  { path: '', pathMatch: 'full', component: ReportDashboardComponent },
  { path: 'uyarilar', component: AlertsPageComponent },
  { path: 'kameralar', component: CameraManagementComponent },
  { path: 'report', component: ReportPageComponent },
  { path: '**', redirectTo: '' },
];

import { Injectable } from '@angular/core';
import * as signalR from '@microsoft/signalr';
import { BehaviorSubject, firstValueFrom } from 'rxjs';
import { HttpClient } from '@angular/common/http';

import { API_CONFIG } from '../config/api.config';
import { ViolationAlert } from '../models/alert.model';

@Injectable({ providedIn: 'root' })
export class AlertSignalrService {
  private readonly connection = new signalR.HubConnectionBuilder()
    .withUrl(API_CONFIG.signalRHubUrl)
    .withAutomaticReconnect()
    .build();

  private readonly alertsSubject = new BehaviorSubject<ViolationAlert[]>([]);
  readonly alerts$ = this.alertsSubject.asObservable();

  constructor(private readonly http: HttpClient) {
    this.connection.on('ReceiveAlert', (alert: ViolationAlert) => {
      const next = [alert, ...this.alertsSubject.value].slice(0, 100);
      this.alertsSubject.next(next);
    });
  }

  async initialize(): Promise<void> {
    const history = await firstValueFrom(
      this.http.get<ViolationAlert[]>(
        `${API_CONFIG.orchestratorBaseUrl}/api/alerts?limit=50`,
      ),
    );
    this.alertsSubject.next(history);

    if (this.connection.state === signalR.HubConnectionState.Disconnected) {
      await this.connection.start();
    }
  }
}

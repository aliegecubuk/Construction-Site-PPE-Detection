export type TelemetrySeverity = 'normal' | 'warning' | 'critical';

export interface CameraTelemetry {
  cameraId: string;
  cameraName: string;
  occurredAt: string;
  gasLevel: number;
  gasSeverity: TelemetrySeverity;
  temperature: number;
  temperatureSeverity: TelemetrySeverity;
  humidity: number;
  humiditySeverity: TelemetrySeverity;
  noiseLevel: number;
  noiseSeverity: TelemetrySeverity;
  vibration: number;
  vibrationSeverity: TelemetrySeverity;
}

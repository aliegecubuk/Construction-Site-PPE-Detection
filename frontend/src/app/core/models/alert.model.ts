export interface ViolationAlert {
  eventId: string;
  cameraId: string;
  cameraName: string;
  violationType: string;
  message: string;
  occurredAt: string;
  frameNumber: number;
}

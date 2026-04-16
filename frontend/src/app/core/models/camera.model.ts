export interface CameraRequirements {
  hardhat: boolean;
  safetyVest: boolean;
  mask: boolean;
}

export interface CameraViewModel {
  cameraId: string;
  name: string;
  streamUrl: string;
  enabled: boolean;
  requirements: CameraRequirements;
}

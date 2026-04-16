const browserHostname =
  typeof window !== 'undefined' && window.location.hostname
    ? window.location.hostname
    : 'localhost';

const orchestratorBaseUrl = `http://${browserHostname}:8080`;

const pythonBaseUrl = `http://${browserHostname}:8000`;

export const API_CONFIG = {
  // .NET orkestratör API:
  //   http://{browser-host}:8080/api/cameras
  orchestratorBaseUrl,

  // Python AI servis API (dogrudan):
  //   http://{browser-host}:8000/api/v1
  pythonBaseUrl,

  // SignalR hub:
  //   http://{browser-host}:8080/hubs/alerts
  signalRHubUrl: `${orchestratorBaseUrl}/hubs/alerts`,
} as const;

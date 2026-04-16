using ReportAi.Orchestrator.Api.Models;

namespace ReportAi.Orchestrator.Api.Services;

public interface IPythonVisionClient
{
    Task PushCameraRequirementsAsync(
        string cameraId,
        CameraRequirementPayload payload,
        CancellationToken cancellationToken);

    Task<CameraTelemetryViewModel?> GetCameraTelemetryAsync(
        string cameraId,
        CancellationToken cancellationToken);

    Task ToggleCameraStatusAsync(
        string cameraId,
        bool enabled,
        CancellationToken cancellationToken);
}

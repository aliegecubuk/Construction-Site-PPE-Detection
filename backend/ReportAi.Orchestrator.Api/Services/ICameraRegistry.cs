using ReportAi.Orchestrator.Api.Models;

namespace ReportAi.Orchestrator.Api.Services;

public interface ICameraRegistry
{
    IReadOnlyCollection<CameraViewModel> GetAll();
    CameraViewModel? Get(string cameraId);
    CameraViewModel UpdateRequirements(string cameraId, CameraRequirementPayload requirements);
    CameraViewModel UpdateStatus(string cameraId, bool enabled);
}

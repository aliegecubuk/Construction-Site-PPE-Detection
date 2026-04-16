using System.Collections.Concurrent;
using Microsoft.Extensions.Options;
using ReportAi.Orchestrator.Api.Models;
using ReportAi.Orchestrator.Api.Options;

namespace ReportAi.Orchestrator.Api.Services;

public sealed class CameraRegistry : ICameraRegistry
{
    private readonly ConcurrentDictionary<string, CameraViewModel> _cameras;

    public CameraRegistry(
        IOptions<CameraCatalogOptions> catalogOptions,
        IOptions<ExternalServiceOptions> externalServiceOptions)
    {
        var pythonBaseUrl = externalServiceOptions.Value.PythonBaseUrl.TrimEnd('/');
        _cameras = new ConcurrentDictionary<string, CameraViewModel>(
            catalogOptions.Value.Cameras.Select(camera =>
                new KeyValuePair<string, CameraViewModel>(
                    camera.CameraId,
                    new CameraViewModel
                    {
                        CameraId = camera.CameraId,
                        Name = camera.Name,
                        StreamUrl = $"{pythonBaseUrl}/api/v1/stream/mjpeg/{camera.CameraId}",
                        Requirements = camera.Requirements
                    })));
    }

    public IReadOnlyCollection<CameraViewModel> GetAll() => _cameras.Values.OrderBy(c => c.CameraId).ToArray();

    public CameraViewModel? Get(string cameraId) =>
        _cameras.TryGetValue(cameraId, out var camera) ? camera : null;

    public CameraViewModel UpdateRequirements(string cameraId, CameraRequirementPayload requirements)
    {
        if (!_cameras.TryGetValue(cameraId, out var existing))
        {
            throw new KeyNotFoundException($"Camera not found: {cameraId}");
        }

        var updated = existing with
        {
            Requirements = requirements
        };
        _cameras[cameraId] = updated;
        return updated;
    }

    public CameraViewModel UpdateStatus(string cameraId, bool enabled)
    {
        if (!_cameras.TryGetValue(cameraId, out var existing))
        {
            throw new KeyNotFoundException($"Camera not found: {cameraId}");
        }

        var updated = existing with
        {
            Enabled = enabled
        };
        _cameras[cameraId] = updated;
        return updated;
    }
}

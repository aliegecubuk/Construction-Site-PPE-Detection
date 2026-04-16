using System.Net.Http.Json;
using Microsoft.Extensions.Options;
using ReportAi.Orchestrator.Api.Models;
using ReportAi.Orchestrator.Api.Options;

namespace ReportAi.Orchestrator.Api.Services;

public sealed class PythonVisionClient : IPythonVisionClient
{
    private readonly HttpClient _httpClient;
    private readonly ExternalServiceOptions _options;

    public PythonVisionClient(
        HttpClient httpClient,
        IOptions<ExternalServiceOptions> options)
    {
        _httpClient = httpClient;
        _options = options.Value;
        _httpClient.Timeout = TimeSpan.FromSeconds(5);
    }

    public async Task PushCameraRequirementsAsync(
        string cameraId,
        CameraRequirementPayload payload,
        CancellationToken cancellationToken)
    {
        // Python endpoint:
        //   PUT http://localhost:8000/api/v1/cameras/{cameraId}/requirements
        var requestUri = $"{_options.PythonBaseUrl.TrimEnd('/')}/api/v1/cameras/{cameraId}/requirements";
        using var response = await _httpClient.PutAsJsonAsync(requestUri, payload, cancellationToken);
        response.EnsureSuccessStatusCode();
    }

    public async Task<CameraTelemetryViewModel?> GetCameraTelemetryAsync(
        string cameraId,
        CancellationToken cancellationToken)
    {
        var requestUri = $"{_options.PythonBaseUrl.TrimEnd('/')}/api/v1/cameras/{cameraId}/telemetry";
        return await _httpClient.GetFromJsonAsync<CameraTelemetryViewModel>(requestUri, cancellationToken);
    }

    public async Task ToggleCameraStatusAsync(
        string cameraId,
        bool enabled,
        CancellationToken cancellationToken)
    {
        var requestUri = $"{_options.PythonBaseUrl.TrimEnd('/')}/api/v1/cameras/{cameraId}";
        // Send a partial update with enabled flag
        using var response = await _httpClient.PutAsJsonAsync(requestUri, new { enabled = enabled }, cancellationToken);
        response.EnsureSuccessStatusCode();
    }
}

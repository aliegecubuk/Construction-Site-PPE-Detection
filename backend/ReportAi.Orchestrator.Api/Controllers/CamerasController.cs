using Microsoft.AspNetCore.Mvc;
using ReportAi.Orchestrator.Api.Models;
using ReportAi.Orchestrator.Api.Services;

namespace ReportAi.Orchestrator.Api.Controllers;

[ApiController]
[Route("api/cameras")]
public sealed class CamerasController : ControllerBase
{
    private readonly ICameraRegistry _cameraRegistry;
    private readonly IPythonVisionClient _pythonVisionClient;

    public CamerasController(
        ICameraRegistry cameraRegistry,
        IPythonVisionClient pythonVisionClient)
    {
        _cameraRegistry = cameraRegistry;
        _pythonVisionClient = pythonVisionClient;
    }

    [HttpGet]
    public ActionResult<IReadOnlyCollection<CameraViewModel>> GetAll()
    {
        // Angular önce bu endpoint'i çağırır.
        // streamUrl alanı Python MJPEG endpoint'ini gösterir:
        //   http://localhost:8000/api/v1/stream/mjpeg/{cameraId}
        return Ok(_cameraRegistry.GetAll());
    }

    [HttpPut("{cameraId}/requirements")]
    public async Task<ActionResult<CameraViewModel>> UpdateRequirements(
        string cameraId,
        [FromBody] CameraRequirementPayload payload,
        CancellationToken cancellationToken)
    {
        if (_cameraRegistry.Get(cameraId) is null)
        {
            return NotFound();
        }

        try
        {
            await _pythonVisionClient.PushCameraRequirementsAsync(cameraId, payload, cancellationToken);
        }
        catch (HttpRequestException exception)
        {
            return StatusCode(StatusCodes.Status502BadGateway, new
            {
                message = "Python vision servisine gereksinim güncellemesi gönderilemedi.",
                detail = exception.Message
            });
        }

        var updated = _cameraRegistry.UpdateRequirements(cameraId, payload);
        return Ok(updated);
    }

    [HttpGet("{cameraId}/telemetry")]
    public async Task<ActionResult<CameraTelemetryViewModel>> GetTelemetry(
        string cameraId,
        CancellationToken cancellationToken)
    {
        if (_cameraRegistry.Get(cameraId) is null)
        {
            return NotFound();
        }

        try
        {
            var telemetry = await _pythonVisionClient.GetCameraTelemetryAsync(cameraId, cancellationToken);
            if (telemetry is null)
            {
                return StatusCode(StatusCodes.Status502BadGateway, new
                {
                    message = "Python vision servisinden telemetri alınamadı."
                });
            }

            return Ok(telemetry);
        }
        catch (HttpRequestException exception)
        {
            return StatusCode(StatusCodes.Status502BadGateway, new
            {
                message = "Python vision servisinden telemetri alınamadı.",
                detail = exception.Message
            });
        }
    }

    [HttpPut("{cameraId}/status")]
    public async Task<ActionResult> ToggleStatus(
        string cameraId,
        [FromQuery] bool enabled,
        CancellationToken cancellationToken)
    {
        if (_cameraRegistry.Get(cameraId) is null)
        {
            return NotFound();
        }

        try
        {
            // Hem Python tarafini sustur hem de .NET registry'sini guncelle
            await _pythonVisionClient.ToggleCameraStatusAsync(cameraId, enabled, cancellationToken);
            _cameraRegistry.UpdateStatus(cameraId, enabled);
            
            return NoContent();
        }
        catch (HttpRequestException exception)
        {
            return StatusCode(StatusCodes.Status502BadGateway, new
            {
                message = "Python vision servisine durum güncellemesi gönderilemedi.",
                detail = exception.Message
            });
        }
    }
}

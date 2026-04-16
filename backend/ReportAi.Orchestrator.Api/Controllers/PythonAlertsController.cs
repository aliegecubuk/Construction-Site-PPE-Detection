using Microsoft.AspNetCore.Mvc;
using ReportAi.Orchestrator.Api.Models;
using ReportAi.Orchestrator.Api.Services;

namespace ReportAi.Orchestrator.Api.Controllers;

[ApiController]
[Route("api/python/violations")]
public sealed class PythonAlertsController : ControllerBase
{
    private readonly IAlertRelayService _alertRelayService;

    public PythonAlertsController(IAlertRelayService alertRelayService)
    {
        _alertRelayService = alertRelayService;
    }

    [HttpPost]
    public async Task<IActionResult> ReceiveViolation(
        [FromBody] PythonViolationEvent payload,
        CancellationToken cancellationToken)
    {
        // Python webhook hedefi:
        //   POST http://localhost:8080/api/python/violations
        await _alertRelayService.RelayAsync(payload, cancellationToken);
        return Accepted();
    }
}

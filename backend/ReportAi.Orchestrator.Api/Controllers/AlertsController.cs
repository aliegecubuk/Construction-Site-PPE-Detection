using Microsoft.AspNetCore.Mvc;
using ReportAi.Orchestrator.Api.Models;
using ReportAi.Orchestrator.Api.Services;

namespace ReportAi.Orchestrator.Api.Controllers;

[ApiController]
[Route("api/alerts")]
public sealed class AlertsController : ControllerBase
{
    private readonly IAlertRelayService _alertRelayService;

    public AlertsController(IAlertRelayService alertRelayService)
    {
        _alertRelayService = alertRelayService;
    }

    [HttpGet]
    public ActionResult<IReadOnlyCollection<PythonViolationEvent>> GetRecent([FromQuery] int limit = 50)
    {
        return Ok(_alertRelayService.GetRecent(Math.Clamp(limit, 1, 200)));
    }
}

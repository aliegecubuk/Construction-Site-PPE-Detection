using Microsoft.AspNetCore.Mvc;
using ReportAi.Orchestrator.Api.Models;
using ReportAi.Orchestrator.Api.Services;

namespace ReportAi.Orchestrator.Api.Controllers;

[ApiController]
[Route("api/reports")]
public sealed class ReportsController : ControllerBase
{
    private readonly IDecisionSupportService _decisionSupportService;

    public ReportsController(IDecisionSupportService decisionSupportService)
    {
        _decisionSupportService = decisionSupportService;
    }

    [HttpGet("decision-support")]
    public ActionResult<DecisionSupportReportViewModel> GetDecisionSupportReport(
        [FromQuery] string? cameraId,
        [FromQuery] int windowMinutes = 30)
    {
        return Ok(_decisionSupportService.GenerateReport(cameraId, Math.Clamp(windowMinutes, 5, 240)));
    }
}

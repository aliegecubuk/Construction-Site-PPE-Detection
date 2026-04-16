using ReportAi.Orchestrator.Api.Models;

namespace ReportAi.Orchestrator.Api.Services;

public interface IDecisionSupportService
{
    DecisionSupportReportViewModel GenerateReport(string? cameraId, int windowMinutes);
}

namespace ReportAi.Orchestrator.Api.Models;

public sealed class DecisionSupportStatsViewModel
{
    public int TotalAlerts { get; init; }
    public int PpeAlerts { get; init; }
    public int IotAlerts { get; init; }
    public int CriticalAlerts { get; init; }
    public int WarningAlerts { get; init; }
    public int DistinctViolationTypes { get; init; }
}

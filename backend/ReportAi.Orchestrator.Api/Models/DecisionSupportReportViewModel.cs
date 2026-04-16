namespace ReportAi.Orchestrator.Api.Models;

public sealed class DecisionSupportReportViewModel
{
    public string Scope { get; init; } = string.Empty;
    public string? CameraId { get; init; }
    public string? CameraName { get; init; }
    public DateTimeOffset GeneratedAt { get; init; }
    public int WindowMinutes { get; init; }
    public string OverallRiskLevel { get; init; } = string.Empty;
    public string ManagerSummary { get; init; } = string.Empty;
    public IReadOnlyCollection<string> InspectionReport { get; init; } = Array.Empty<string>();
    public IReadOnlyCollection<string> PreventiveRecommendations { get; init; } = Array.Empty<string>();
    public IReadOnlyCollection<RiskCategoryViewModel> RiskCategories { get; init; } = Array.Empty<RiskCategoryViewModel>();
    public DecisionSupportStatsViewModel Statistics { get; init; } = new();
}

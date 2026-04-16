namespace ReportAi.Orchestrator.Api.Models;

public sealed class RiskCategoryViewModel
{
    public string CategoryName { get; init; } = string.Empty;
    public string RiskLevel { get; init; } = string.Empty;
    public int OccurrenceCount { get; init; }
    public string Narrative { get; init; } = string.Empty;
    public string Recommendation { get; init; } = string.Empty;
    public IReadOnlyCollection<string> SampleViolations { get; init; } = Array.Empty<string>();
}

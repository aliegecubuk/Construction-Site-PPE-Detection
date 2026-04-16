namespace ReportAi.Orchestrator.Api.Options;

public sealed class ExternalServiceOptions
{
    public const string SectionName = "ExternalServices";

    public string PythonBaseUrl { get; init; } = "http://localhost:8000";
}

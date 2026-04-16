namespace ReportAi.Orchestrator.Api.Models;

public sealed record CameraViewModel
{
    public string CameraId { get; init; } = string.Empty;
    public string Name { get; init; } = string.Empty;
    public string StreamUrl { get; init; } = string.Empty;
    public bool Enabled { get; init; } = true;
    public CameraRequirementPayload Requirements { get; init; } = new();
}

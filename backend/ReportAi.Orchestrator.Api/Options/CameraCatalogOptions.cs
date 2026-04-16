using ReportAi.Orchestrator.Api.Models;

namespace ReportAi.Orchestrator.Api.Options;

public sealed class CameraCatalogOptions
{
    public const string SectionName = "CameraCatalog";

    public List<CameraCatalogEntry> Cameras { get; init; } = [];
}

public sealed class CameraCatalogEntry
{
    public string CameraId { get; init; } = string.Empty;
    public string Name { get; init; } = string.Empty;
    public CameraRequirementPayload Requirements { get; init; } = new();
}

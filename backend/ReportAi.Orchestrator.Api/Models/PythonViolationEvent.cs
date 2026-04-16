using System.Text.Json.Serialization;

namespace ReportAi.Orchestrator.Api.Models;

public sealed class PythonViolationEvent
{
    [JsonPropertyName("eventId")]
    public string EventId { get; init; } = string.Empty;

    [JsonPropertyName("cameraId")]
    public string CameraId { get; init; } = string.Empty;

    [JsonPropertyName("cameraName")]
    public string CameraName { get; init; } = string.Empty;

    [JsonPropertyName("violationType")]
    public string ViolationType { get; init; } = string.Empty;

    [JsonPropertyName("message")]
    public string Message { get; init; } = string.Empty;

    [JsonPropertyName("occurredAt")]
    public DateTimeOffset OccurredAt { get; init; }

    [JsonPropertyName("frameNumber")]
    public int FrameNumber { get; init; }
}

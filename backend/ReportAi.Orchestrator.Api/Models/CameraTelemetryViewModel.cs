using System.Text.Json.Serialization;

namespace ReportAi.Orchestrator.Api.Models;

public sealed class CameraTelemetryViewModel
{
    [JsonPropertyName("cameraId")]
    public string CameraId { get; init; } = string.Empty;

    [JsonPropertyName("cameraName")]
    public string CameraName { get; init; } = string.Empty;

    [JsonPropertyName("occurredAt")]
    public DateTimeOffset OccurredAt { get; init; }

    [JsonPropertyName("gasLevel")]
    public double GasLevel { get; init; }

    [JsonPropertyName("gasSeverity")]
    public string GasSeverity { get; init; } = "normal";

    [JsonPropertyName("temperature")]
    public double Temperature { get; init; }

    [JsonPropertyName("temperatureSeverity")]
    public string TemperatureSeverity { get; init; } = "normal";

    [JsonPropertyName("humidity")]
    public double Humidity { get; init; }

    [JsonPropertyName("humiditySeverity")]
    public string HumiditySeverity { get; init; } = "normal";

    [JsonPropertyName("noiseLevel")]
    public double NoiseLevel { get; init; }

    [JsonPropertyName("noiseSeverity")]
    public string NoiseSeverity { get; init; } = "normal";

    [JsonPropertyName("vibration")]
    public double Vibration { get; init; }

    [JsonPropertyName("vibrationSeverity")]
    public string VibrationSeverity { get; init; } = "normal";
}

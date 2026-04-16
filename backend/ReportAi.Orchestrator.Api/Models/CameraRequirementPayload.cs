using System.Text.Json.Serialization;

namespace ReportAi.Orchestrator.Api.Models;

public sealed class CameraRequirementPayload
{
    [JsonPropertyName("hardhat")]
    public bool Hardhat { get; init; }

    [JsonPropertyName("safetyVest")]
    public bool SafetyVest { get; init; }

    [JsonPropertyName("mask")]
    public bool Mask { get; init; }
}

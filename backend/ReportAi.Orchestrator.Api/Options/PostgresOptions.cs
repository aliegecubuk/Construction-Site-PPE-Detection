namespace ReportAi.Orchestrator.Api.Options;

public sealed class PostgresOptions
{
    public const string SectionName = "Postgres";

    public string ConnectionString { get; init; } = string.Empty;
}

using Microsoft.Extensions.Options;
using Npgsql;
using ReportAi.Orchestrator.Api.Models;
using ReportAi.Orchestrator.Api.Options;

namespace ReportAi.Orchestrator.Api.Services;

public sealed class PostgresAlertStore : IAlertStore
{
    private readonly string _connectionString;

    public PostgresAlertStore(IOptions<PostgresOptions> postgresOptions)
    {
        _connectionString = postgresOptions.Value.ConnectionString;

        if (string.IsNullOrWhiteSpace(_connectionString))
        {
            throw new InvalidOperationException("Postgres connection string is not configured.");
        }
    }

    public async Task InitializeAsync(CancellationToken cancellationToken)
    {
        const string sql = """
            CREATE SCHEMA IF NOT EXISTS report_ai;

            CREATE TABLE IF NOT EXISTS report_ai.alert_events (
                event_id text PRIMARY KEY,
                camera_id text NOT NULL,
                camera_name text NOT NULL,
                violation_type text NOT NULL,
                message text NOT NULL,
                occurred_at timestamptz NOT NULL,
                frame_number integer NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_alert_events_occurred_at
                ON report_ai.alert_events (occurred_at DESC);

            CREATE INDEX IF NOT EXISTS idx_alert_events_camera_id_occurred_at
                ON report_ai.alert_events (camera_id, occurred_at DESC);
            """;

        await using var connection = new NpgsqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);
        await using var command = new NpgsqlCommand(sql, connection);
        await command.ExecuteNonQueryAsync(cancellationToken);
    }

    public async Task SaveAsync(PythonViolationEvent alert, CancellationToken cancellationToken)
    {
        const string sql = """
            INSERT INTO report_ai.alert_events (
                event_id,
                camera_id,
                camera_name,
                violation_type,
                message,
                occurred_at,
                frame_number
            )
            VALUES (
                @event_id,
                @camera_id,
                @camera_name,
                @violation_type,
                @message,
                @occurred_at,
                @frame_number
            )
            ON CONFLICT (event_id) DO NOTHING;
            """;

        await using var connection = new NpgsqlConnection(_connectionString);
        await connection.OpenAsync(cancellationToken);

        await using var command = new NpgsqlCommand(sql, connection);
        command.Parameters.AddWithValue("event_id", alert.EventId);
        command.Parameters.AddWithValue("camera_id", alert.CameraId);
        command.Parameters.AddWithValue("camera_name", alert.CameraName);
        command.Parameters.AddWithValue("violation_type", alert.ViolationType);
        command.Parameters.AddWithValue("message", alert.Message);
        command.Parameters.AddWithValue("occurred_at", alert.OccurredAt.UtcDateTime);
        command.Parameters.AddWithValue("frame_number", alert.FrameNumber);

        await command.ExecuteNonQueryAsync(cancellationToken);
    }

    public IReadOnlyCollection<PythonViolationEvent> GetRecent(int limit)
    {
        const string sql = """
            SELECT
                event_id,
                camera_id,
                camera_name,
                violation_type,
                message,
                occurred_at,
                frame_number
            FROM report_ai.alert_events
            ORDER BY occurred_at DESC
            LIMIT @limit;
            """;

        return ExecuteQuery(sql, command =>
        {
            command.Parameters.AddWithValue("limit", limit);
        });
    }

    public IReadOnlyCollection<PythonViolationEvent> Query(string? cameraId, DateTimeOffset since)
    {
        const string sql = """
            SELECT
                event_id,
                camera_id,
                camera_name,
                violation_type,
                message,
                occurred_at,
                frame_number
            FROM report_ai.alert_events
            WHERE occurred_at >= @since
              AND (@camera_id IS NULL OR camera_id = @camera_id)
            ORDER BY occurred_at DESC;
            """;

        return ExecuteQuery(sql, command =>
        {
            command.Parameters.AddWithValue("since", since);
            command.Parameters.AddWithValue("camera_id", (object?)cameraId ?? DBNull.Value);
        });
    }

    private IReadOnlyCollection<PythonViolationEvent> ExecuteQuery(
        string sql,
        Action<NpgsqlCommand> configure)
    {
        using var connection = new NpgsqlConnection(_connectionString);
        connection.Open();

        using var command = new NpgsqlCommand(sql, connection);
        configure(command);

        using var reader = command.ExecuteReader();
        var alerts = new List<PythonViolationEvent>();

        while (reader.Read())
        {
            alerts.Add(new PythonViolationEvent
            {
                EventId = reader.GetString(0),
                CameraId = reader.GetString(1),
                CameraName = reader.GetString(2),
                ViolationType = reader.GetString(3),
                Message = reader.GetString(4),
                OccurredAt = new DateTimeOffset(
                    DateTime.SpecifyKind(reader.GetDateTime(5), DateTimeKind.Utc)),
                FrameNumber = reader.GetInt32(6)
            });
        }

        return alerts;
    }
}

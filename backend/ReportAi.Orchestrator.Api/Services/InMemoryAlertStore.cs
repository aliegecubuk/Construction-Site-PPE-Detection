using ReportAi.Orchestrator.Api.Models;

namespace ReportAi.Orchestrator.Api.Services;

public sealed class InMemoryAlertStore : IAlertStore
{
    private readonly List<PythonViolationEvent> _alerts = new();
    private readonly object _lock = new();

    public Task InitializeAsync(CancellationToken cancellationToken)
    {
        return Task.CompletedTask;
    }

    public Task SaveAsync(PythonViolationEvent alert, CancellationToken cancellationToken)
    {
        lock (_lock)
        {
            if (!_alerts.Any(a => a.EventId == alert.EventId))
            {
                _alerts.Add(alert);
            }
        }
        return Task.CompletedTask;
    }

    public IReadOnlyCollection<PythonViolationEvent> GetRecent(int limit)
    {
        lock (_lock)
        {
            return _alerts.OrderByDescending(a => a.OccurredAt).Take(limit).ToList();
        }
    }

    public IReadOnlyCollection<PythonViolationEvent> Query(string? cameraId, DateTimeOffset since)
    {
        lock (_lock)
        {
            return _alerts
                .Where(a => a.OccurredAt >= since)
                .Where(a => string.IsNullOrEmpty(cameraId) || a.CameraId == cameraId)
                .OrderByDescending(a => a.OccurredAt)
                .ToList();
        }
    }
}

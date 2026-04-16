using ReportAi.Orchestrator.Api.Models;

namespace ReportAi.Orchestrator.Api.Services;

public interface IAlertRelayService
{
    Task RelayAsync(PythonViolationEvent alert, CancellationToken cancellationToken);
    IReadOnlyCollection<PythonViolationEvent> GetRecent(int limit);
    IReadOnlyCollection<PythonViolationEvent> Query(string? cameraId, DateTimeOffset since);
}

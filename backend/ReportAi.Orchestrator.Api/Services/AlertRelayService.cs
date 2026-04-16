using Microsoft.AspNetCore.SignalR;
using ReportAi.Orchestrator.Api.Hubs;
using ReportAi.Orchestrator.Api.Models;

namespace ReportAi.Orchestrator.Api.Services;

public sealed class AlertRelayService : IAlertRelayService
{
    private readonly IHubContext<AlertsHub> _hubContext;
    private readonly IAlertStore _alertStore;

    public AlertRelayService(IHubContext<AlertsHub> hubContext, IAlertStore alertStore)
    {
        _hubContext = hubContext;
        _alertStore = alertStore;
    }

    public async Task RelayAsync(PythonViolationEvent alert, CancellationToken cancellationToken)
    {
        await _alertStore.SaveAsync(alert, cancellationToken);
        await _hubContext.Clients.All.SendAsync("ReceiveAlert", alert, cancellationToken);
    }

    public IReadOnlyCollection<PythonViolationEvent> GetRecent(int limit) =>
        _alertStore.GetRecent(limit);

    public IReadOnlyCollection<PythonViolationEvent> Query(string? cameraId, DateTimeOffset since) =>
        _alertStore.Query(cameraId, since);
}

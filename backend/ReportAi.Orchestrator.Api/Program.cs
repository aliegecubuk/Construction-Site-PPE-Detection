using ReportAi.Orchestrator.Api.Hubs;
using ReportAi.Orchestrator.Api.Options;
using ReportAi.Orchestrator.Api.Services;

var builder = WebApplication.CreateBuilder(args);

// Varsayılan portlar:
// Angular UI:      http://localhost:4200
// .NET Orchestrator: http://localhost:8080
// Python FastAPI:  http://localhost:8000
builder.WebHost.UseUrls("http://0.0.0.0:8080");

builder.Services.Configure<ExternalServiceOptions>(
    builder.Configuration.GetSection(ExternalServiceOptions.SectionName));
builder.Services.Configure<CameraCatalogOptions>(
    builder.Configuration.GetSection(CameraCatalogOptions.SectionName));
builder.Services.Configure<PostgresOptions>(
    builder.Configuration.GetSection(PostgresOptions.SectionName));

builder.Services.AddHttpClient<IPythonVisionClient, PythonVisionClient>();
builder.Services.AddSingleton<ICameraRegistry, CameraRegistry>();
builder.Services.AddSingleton<IAlertStore, InMemoryAlertStore>();
builder.Services.AddSingleton<IAlertRelayService, AlertRelayService>();
builder.Services.AddSingleton<IDecisionSupportService, DecisionSupportService>();

builder.Services.AddControllers();
builder.Services.AddSignalR();

builder.Services.AddCors(options =>
{
    options.AddPolicy("Frontend", policy =>
    {
        policy
            .WithOrigins(
                "http://localhost:4200",
                "http://127.0.0.1:4200")
            .AllowAnyHeader()
            .AllowAnyMethod()
            .AllowCredentials();
    });
});

var app = builder.Build();

await app.Services.GetRequiredService<IAlertStore>().InitializeAsync(CancellationToken.None);

app.UseCors("Frontend");

app.MapControllers();

// Angular SignalR istemcisi bu hub'a bağlanır:
//   ws://localhost:8080/hubs/alerts
app.MapHub<AlertsHub>("/hubs/alerts");

app.Run();

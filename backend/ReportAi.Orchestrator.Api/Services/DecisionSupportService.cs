using ReportAi.Orchestrator.Api.Models;

namespace ReportAi.Orchestrator.Api.Services;

public sealed class DecisionSupportService : IDecisionSupportService
{
    private readonly IAlertRelayService _alertRelayService;
    private readonly ICameraRegistry _cameraRegistry;

    public DecisionSupportService(
        IAlertRelayService alertRelayService,
        ICameraRegistry cameraRegistry)
    {
        _alertRelayService = alertRelayService;
        _cameraRegistry = cameraRegistry;
    }

    public DecisionSupportReportViewModel GenerateReport(string? cameraId, int windowMinutes)
    {
        var windowStart = DateTimeOffset.UtcNow.AddMinutes(-windowMinutes);
        var scopedAlerts = _alertRelayService.Query(cameraId, windowStart).ToArray();
        if (scopedAlerts.Length == 0)
        {
            scopedAlerts = _alertRelayService
                .GetRecent(250)
                .Where(alert =>
                    string.IsNullOrWhiteSpace(cameraId) ||
                    string.Equals(alert.CameraId, cameraId, StringComparison.OrdinalIgnoreCase))
                .ToArray();
        }
        var camera = !string.IsNullOrWhiteSpace(cameraId) ? _cameraRegistry.Get(cameraId) : null;

        var stats = BuildStats(scopedAlerts);
        var riskCategories = BuildRiskCategories(scopedAlerts);
        var overallRiskLevel = ResolveOverallRisk(scopedAlerts, riskCategories);
        var recommendations = riskCategories
            .OrderByDescending(category => category.OccurrenceCount)
            .Select(category => category.Recommendation)
            .Distinct(StringComparer.Ordinal)
            .Take(5)
            .ToArray();

        return new DecisionSupportReportViewModel
        {
            Scope = camera is null ? "all-cameras" : "single-camera",
            CameraId = camera?.CameraId,
            CameraName = camera?.Name,
            GeneratedAt = DateTimeOffset.UtcNow,
            WindowMinutes = windowMinutes,
            OverallRiskLevel = overallRiskLevel,
            ManagerSummary = BuildManagerSummary(camera?.Name, windowMinutes, stats, overallRiskLevel, riskCategories),
            InspectionReport = BuildInspectionReport(camera?.Name, windowMinutes, scopedAlerts, riskCategories),
            PreventiveRecommendations = recommendations,
            RiskCategories = riskCategories,
            Statistics = stats
        };
    }

    private static DecisionSupportStatsViewModel BuildStats(IReadOnlyCollection<PythonViolationEvent> alerts)
    {
        return new DecisionSupportStatsViewModel
        {
            TotalAlerts = alerts.Count,
            PpeAlerts = alerts.Count(IsPpeAlert),
            IotAlerts = alerts.Count(IsIotAlert),
            CriticalAlerts = alerts.Count(IsCriticalAlert),
            WarningAlerts = alerts.Count(IsWarningAlert),
            DistinctViolationTypes = alerts
                .Select(alert => alert.ViolationType)
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .Count()
        };
    }

    private static IReadOnlyCollection<RiskCategoryViewModel> BuildRiskCategories(
        IReadOnlyCollection<PythonViolationEvent> alerts)
    {
        var ppeAlerts = alerts.Where(IsPpeAlert).ToArray();
        var iotAlerts = alerts.Where(IsIotAlert).ToArray();
        var repeatedAlerts = alerts
            .GroupBy(alert => new { alert.CameraId, alert.ViolationType })
            .Where(group => group.Count() >= 3)
            .SelectMany(group => group)
            .ToArray();

        var categories = new List<RiskCategoryViewModel>();

        if (ppeAlerts.Length > 0)
        {
            categories.Add(new RiskCategoryViewModel
            {
                CategoryName = "KKD Uyum Riski",
                RiskLevel = ResolveCategoryRisk(ppeAlerts.Length, ppeAlerts.Any(IsCriticalAlert)),
                OccurrenceCount = ppeAlerts.Length,
                Narrative = $"Pencere içinde {ppeAlerts.Length} adet KKD ihlali gözlendi. En sık eksikler: {JoinTopViolations(ppeAlerts)}.",
                Recommendation = "Giriş noktalarında KKD kontrolünü sıkılaştırın, vardiya başlangıcında kısa PPE doğrulaması uygulayın ve sahaya çıkış öncesi eksik ekipman dağıtımını zorunlu hale getirin.",
                SampleViolations = ppeAlerts.Select(alert => alert.ViolationType).Distinct().Take(3).ToArray()
            });
        }

        if (iotAlerts.Length > 0)
        {
            categories.Add(new RiskCategoryViewModel
            {
                CategoryName = "Çevresel Koşul Riski",
                RiskLevel = ResolveCategoryRisk(iotAlerts.Length, iotAlerts.Any(IsCriticalAlert)),
                OccurrenceCount = iotAlerts.Length,
                Narrative = $"Dummy IoT telemetrisi aynı pencerede {iotAlerts.Length} uyarı üretti. Baskın çevresel riskler: {JoinTopViolations(iotAlerts)}.",
                Recommendation = "Kritik sensör tipleri için eşik aşımlarında otomatik saha anonsu, bölgesel yavaşlatma ve kaynak ekipman kontrol prosedürü devreye alınmalıdır.",
                SampleViolations = iotAlerts.Select(alert => alert.ViolationType).Distinct().Take(3).ToArray()
            });
        }

        if (repeatedAlerts.Length > 0)
        {
            categories.Add(new RiskCategoryViewModel
            {
                CategoryName = "Tekrarlayan İhlal Paterni",
                RiskLevel = ResolveCategoryRisk(repeatedAlerts.Length, repeatedAlerts.Any(IsCriticalAlert)),
                OccurrenceCount = repeatedAlerts.Length,
                Narrative = $"Aynı kamera ve aynı ihlal tipi en az üç kez tekrarlandı. Bu durum davranışsal alışkanlık veya süreç açığı olduğuna işaret ediyor.",
                Recommendation = "Tekrarlayan ihlaller için sorumlu ekip liderine görev atayın, alan bazlı kök neden analizi yapın ve doğrulama checklist'ini kamera özelinde güncelleyin.",
                SampleViolations = repeatedAlerts.Select(alert => alert.ViolationType).Distinct().Take(3).ToArray()
            });
        }

        if (categories.Count == 0)
        {
            categories.Add(new RiskCategoryViewModel
            {
                CategoryName = "Operasyonel Durum",
                RiskLevel = "low",
                OccurrenceCount = 0,
                Narrative = "İncelenen pencerede anlamlı bir risk paterni oluşmadı.",
                Recommendation = "Mevcut konfigürasyonu koruyun ve rutin izlemeye devam edin.",
                SampleViolations = Array.Empty<string>()
            });
        }

        return categories;
    }

    private static string BuildManagerSummary(
        string? cameraName,
        int windowMinutes,
        DecisionSupportStatsViewModel stats,
        string overallRiskLevel,
        IReadOnlyCollection<RiskCategoryViewModel> riskCategories)
    {
        var scopeLabel = string.IsNullOrWhiteSpace(cameraName) ? "tüm saha" : cameraName;
        var topCategory = riskCategories.OrderByDescending(category => category.OccurrenceCount).First();

        return $"{scopeLabel} için son {windowMinutes} dakikalık pencerede {stats.TotalAlerts} alert üretildi. " +
               $"Genel risk seviyesi {overallRiskLevel}. KKD kaynaklı uyarı sayısı {stats.PpeAlerts}, " +
               $"IoT/çevresel kaynaklı uyarı sayısı {stats.IotAlerts}. " +
               $"Baskın risk kategorisi '{topCategory.CategoryName}' olarak değerlendirildi; bu kategori için temel bulgu: {topCategory.Narrative}";
    }

    private static IReadOnlyCollection<string> BuildInspectionReport(
        string? cameraName,
        int windowMinutes,
        IReadOnlyCollection<PythonViolationEvent> alerts,
        IReadOnlyCollection<RiskCategoryViewModel> riskCategories)
    {
        if (alerts.Count == 0)
        {
            return new[]
            {
                $"{(cameraName ?? "Saha")} için son {windowMinutes} dakikada ihlal tespit edilmedi.",
                "Mevcut konfigürasyon altında sistem veri topluyor ancak müdahale gerektiren risk oluşmadı.",
                "Rutin izleme, vardiya öncesi KKD kontrolü ve eşik tabanlı IoT alarm doğrulaması yeterli görünüyor."
            };
        }

        var latest = alerts
            .OrderByDescending(alert => alert.OccurredAt)
            .Take(3)
            .Select(alert => $"{alert.CameraName}: {alert.ViolationType}")
            .ToArray();

        return new[]
        {
            $"{(cameraName ?? "Saha geneli")} için son {windowMinutes} dakikalık alert penceresi incelendi ve {alerts.Count} kayıt değerlendirildi.",
            $"Son olay örnekleri: {string.Join(", ", latest)}.",
            $"Risk analizi sonucunda {string.Join("; ", riskCategories.Select(category => $"{category.CategoryName}={category.RiskLevel}"))} dağılımı oluştu.",
            "Bu çıktı yalnızca veri depolayan bir kayıt sistemi değil, müdahale sırasını belirleyen karar destek katmanı olarak yorumlanmalıdır."
        };
    }

    private static string ResolveOverallRisk(
        IReadOnlyCollection<PythonViolationEvent> alerts,
        IReadOnlyCollection<RiskCategoryViewModel> categories)
    {
        if (alerts.Count == 0)
        {
            return "low";
        }

        var score = 0;
        foreach (var alert in alerts)
        {
            score += IsCriticalAlert(alert) ? 4 : 2;
            if (IsPpeAlert(alert))
            {
                score += 1;
            }
        }

        if (categories.Any(category => string.Equals(category.RiskLevel, "critical", StringComparison.OrdinalIgnoreCase)))
        {
            score += 4;
        }

        return score switch
        {
            >= 28 => "critical",
            >= 16 => "high",
            >= 8 => "medium",
            _ => "low"
        };
    }

    private static string ResolveCategoryRisk(int occurrenceCount, bool hasCritical) =>
        hasCritical
            ? "critical"
            : occurrenceCount >= 8
                ? "high"
                : occurrenceCount >= 3
                    ? "medium"
                    : "low";

    private static string JoinTopViolations(IEnumerable<PythonViolationEvent> alerts) =>
        string.Join(
            ", ",
            alerts.GroupBy(alert => alert.ViolationType)
                .OrderByDescending(group => group.Count())
                .Take(3)
                .Select(group => $"{group.Key} ({group.Count()})"));

    private static bool IsIotAlert(PythonViolationEvent alert) =>
        alert.ViolationType.StartsWith("IoT ", StringComparison.OrdinalIgnoreCase);

    private static bool IsPpeAlert(PythonViolationEvent alert) => !IsIotAlert(alert);

    private static bool IsCriticalAlert(PythonViolationEvent alert) =>
        alert.ViolationType.Contains("Kritik", StringComparison.OrdinalIgnoreCase);

    private static bool IsWarningAlert(PythonViolationEvent alert) =>
        alert.ViolationType.Contains("Uyarı", StringComparison.OrdinalIgnoreCase);
}

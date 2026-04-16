export interface DecisionSupportStats {
  totalAlerts: number;
  ppeAlerts: number;
  iotAlerts: number;
  criticalAlerts: number;
  warningAlerts: number;
  distinctViolationTypes: number;
}

export interface RiskCategory {
  categoryName: string;
  riskLevel: string;
  occurrenceCount: number;
  narrative: string;
  recommendation: string;
  sampleViolations: string[];
}

export interface DecisionSupportReport {
  scope: string;
  cameraId?: string;
  cameraName?: string;
  generatedAt: string;
  windowMinutes: number;
  overallRiskLevel: string;
  managerSummary: string;
  inspectionReport: string[];
  preventiveRecommendations: string[];
  riskCategories: RiskCategory[];
  statistics: DecisionSupportStats;
}

import { get, post } from "./client";

export function getMlMetrics() {
  return get("/api/ml/metrics");
}

export function getMlSummary(params) {
  return get("/api/ml/summary", params);
}

export function getMlAnalytics() {
  return get("/api/ml/analytics");
}

export function predictCase(caseId) {
  return post(`/api/ml/predict/${caseId}`, {});
}

export function predictBatch(body) {
  return post("/api/ml/predict/batch", body || {});
}

export function getPredictionHistory(caseId) {
  return get(`/api/ml/predictions/${caseId}`);
}

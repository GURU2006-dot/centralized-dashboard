import { get, patch, post } from "./client";

export function listAlerts(params) {
  return get("/api/alerts", params);
}

export function evaluateAlerts() {
  return post("/api/alerts/evaluate", {});
}

export function markAlertRead(id) {
  return patch(`/api/alerts/${id}/read`, {});
}

import { get } from "./client";

export function getKpis(params) {
  return get("/api/dashboard/kpis", params);
}

export function getCharts(params) {
  return get("/api/dashboard/charts", params);
}

export function getFilters() {
  return get("/api/dashboard/filters");
}

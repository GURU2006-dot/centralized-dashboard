import { get, post } from "./client";

export function getIntegrationStatus() {
  return get("/api/integrations/status");
}

export function lookupIntegration(system, ulpin) {
  return post(`/api/integrations/${system}/lookup`, { ulpin });
}

export function syncIntegration(system) {
  return post(`/api/integrations/${system}/sync`, {});
}

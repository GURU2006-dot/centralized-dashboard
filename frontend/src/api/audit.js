import { get } from "./client";

export function listAudit(params) {
  return get("/api/audit", params);
}

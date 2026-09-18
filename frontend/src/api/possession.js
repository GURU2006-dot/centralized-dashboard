import { get, patch, post } from "./client";

export function getPossession(caseId) {
  return get(`/api/possession/${caseId}`);
}

export function createPossession(body) {
  return post("/api/possession", body);
}

export function updatePossession(caseId, body) {
  return patch(`/api/possession/${caseId}`, body);
}

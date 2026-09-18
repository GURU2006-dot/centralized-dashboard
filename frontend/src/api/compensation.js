import { get, patch, post } from "./client";

export function getCompensation(caseId) {
  return get(`/api/compensation/${caseId}`);
}

export function createCompensation(body) {
  return post("/api/compensation", body);
}

export function updateCompensation(caseId, body) {
  return patch(`/api/compensation/${caseId}`, body);
}

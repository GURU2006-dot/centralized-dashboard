import { get, patch, post } from "./client";

export function getRehab(caseId) {
  return get(`/api/rehabilitation/${caseId}`);
}

export function createRehab(body) {
  return post("/api/rehabilitation", body);
}

export function updateRehab(id, body) {
  return patch(`/api/rehabilitation/${id}`, body);
}

export function getResettlement(caseId) {
  return get(`/api/resettlement/${caseId}`);
}

export function createResettlement(body) {
  return post("/api/resettlement", body);
}

export function updateResettlement(id, body) {
  return patch(`/api/resettlement/${id}`, body);
}

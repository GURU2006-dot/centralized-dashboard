import { get, post } from "./client";

export function listAcquisitions(params) {
  return get("/api/acquisitions", params);
}

export function getAcquisition(id) {
  return get(`/api/acquisitions/${id}`);
}

export function getTimeline(id) {
  return get(`/api/acquisitions/${id}/timeline`);
}

export function transitionCase(id, to_stage, remarks) {
  return post(`/api/acquisitions/${id}/transition`, { to_stage, remarks });
}

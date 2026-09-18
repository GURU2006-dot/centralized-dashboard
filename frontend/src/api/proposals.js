import { get, patch, post } from "./client";

export function listProposals(params) {
  return get("/api/proposals", params);
}

export function getProposal(id) {
  return get(`/api/proposals/${id}`);
}

export function createProposal(body) {
  return post("/api/proposals", body);
}

export function updateProposal(id, body) {
  return patch(`/api/proposals/${id}`, body);
}

export function submitProposal(id, remarks) {
  return post(`/api/proposals/${id}/submit`, { remarks });
}

export function verifyProposal(id, remarks) {
  return post(`/api/proposals/${id}/verify`, { remarks });
}

export function approveProposal(id, remarks) {
  return post(`/api/proposals/${id}/approve`, { remarks });
}

export function rejectProposal(id, remarks) {
  return post(`/api/proposals/${id}/reject`, { remarks });
}

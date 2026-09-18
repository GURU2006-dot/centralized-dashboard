import { get, patch, post } from "./client";

export function listFamilies(params) {
  return get("/api/families", params);
}

export function getFamily(id) {
  return get(`/api/families/${id}`);
}

export function createFamily(body) {
  return post("/api/families", body);
}

export function updateFamily(id, body) {
  return patch(`/api/families/${id}`, body);
}

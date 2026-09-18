import { get, patch, post } from "./client";

export function listProjects(params) {
  return get("/api/projects", params);
}

export function getProject(id) {
  return get(`/api/projects/${id}`);
}

export function createProject(body) {
  return post("/api/projects", body);
}

export function updateProject(id, body) {
  return patch(`/api/projects/${id}`, body);
}

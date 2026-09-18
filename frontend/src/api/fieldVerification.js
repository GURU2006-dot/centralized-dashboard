import { get, patch, post, postForm } from "./client";

export function listField(params) {
  return get("/api/field-verification", params);
}

export function getField(id) {
  return get(`/api/field-verification/${id}`);
}

export function updateField(id, body) {
  return patch(`/api/field-verification/${id}`, body);
}

export function submitField(id, remarks) {
  return post(`/api/field-verification/${id}/submit`, { remarks });
}

export function uploadFieldPhoto(id, file) {
  const form = new FormData();
  form.append("file", file);
  return postForm(`/api/field-verification/${id}/photos`, form);
}

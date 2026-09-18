import { get, patch, postForm } from "./client";

export function listDocuments(params) {
  return get("/api/documents", params);
}

export function getDocument(id) {
  return get(`/api/documents/${id}`);
}

export function uploadDocument({ file, name, doc_type, project_id, parcel_id, proposal_id, acquisition_case_id }) {
  const form = new FormData();
  form.append("file", file);
  if (name) form.append("name", name);
  if (doc_type) form.append("doc_type", doc_type);
  if (project_id) form.append("project_id", project_id);
  if (parcel_id) form.append("parcel_id", parcel_id);
  if (proposal_id) form.append("proposal_id", proposal_id);
  if (acquisition_case_id) form.append("acquisition_case_id", acquisition_case_id);
  return postForm("/api/documents", form);
}

export function verifyDocument(id, verification_status, remarks) {
  return patch(`/api/documents/${id}`, { verification_status, remarks });
}

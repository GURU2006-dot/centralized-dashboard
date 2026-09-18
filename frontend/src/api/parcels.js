import { get } from "./client";

export function listParcels(params) {
  return get("/api/parcels", params);
}

export function getParcel(id) {
  return get(`/api/parcels/${id}`);
}

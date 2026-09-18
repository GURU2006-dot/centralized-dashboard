import { get } from "./client";

export function getParcelGeojson(params) {
  return get("/api/gis/parcels", params);
}

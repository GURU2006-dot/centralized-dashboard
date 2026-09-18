import { get, patch } from "./client";

export function listNotifications(params) {
  return get("/api/notifications", params);
}

export function markNotificationRead(id) {
  return patch(`/api/notifications/${id}/read`, {});
}

export function markAllNotificationsRead() {
  return patch("/api/notifications/read-all", {});
}

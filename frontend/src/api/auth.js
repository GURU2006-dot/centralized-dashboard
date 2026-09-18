import { get, post } from "./client";

export function login(email, password) {
  return post("/api/auth/login", { email, password });
}

export function me() {
  return get("/api/auth/me");
}

import axios from "axios";

const TOKEN_KEY = "nlamp_token";
const USER_KEY = "nlamp_user";

export function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  try {
    const raw = sessionStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setSession(token, user) {
  if (token) sessionStorage.setItem(TOKEN_KEY, token);
  if (user) sessionStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
}

const client = axios.create({
  baseURL: "",
  timeout: 30000,
});

client.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (err) => {
    const status = err.response?.status;
    if (status === 401) {
      clearSession();
      const path = window.location.pathname;
      if (path !== "/login") {
        window.location.assign("/login");
      }
    }
    const payload = err.response?.data?.error;
    const error = new Error(payload?.message || err.message || "Request failed");
    error.status = status;
    error.code = payload?.code;
    error.details = payload?.details;
    throw error;
  },
);

export async function get(url, params) {
  const { data } = await client.get(url, { params });
  return data;
}

export async function post(url, body) {
  const { data } = await client.post(url, body);
  return data;
}

export async function patch(url, body) {
  const { data } = await client.patch(url, body);
  return data;
}

export async function postForm(url, formData) {
  const { data } = await client.post(url, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export default client;

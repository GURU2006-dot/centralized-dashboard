import { spawn } from "node:child_process";

const chrome = spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", [
  "--headless=new",
  "--remote-debugging-port=9222",
  "--user-data-dir=C:\\Users\\bhanu\\AppData\\Local\\Temp\\chrome-fetch-test3",
  "--disable-gpu",
  "--no-first-run",
  "--no-default-browser-check",
]);

async function waitReady() {
  for (let i = 0; i < 25; i++) {
    try {
      const res = await fetch("http://localhost:9222/json/version");
      if (res.ok) return await res.json();
    } catch {}
    await new Promise((r) => setTimeout(r, 200));
  }
  throw new Error("Chrome not ready");
}

await waitReady();

const newTabRes = await fetch("http://localhost:9222/json/new?about:blank", { method: "PUT" });
const tab = await newTabRes.json();
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r));

let id = 1;
const callbacks = new Map();

function send(method, params = {}) {
  const reqId = id++;
  return new Promise((resolve) => {
    callbacks.set(reqId, resolve);
    ws.send(JSON.stringify({ id: reqId, method, params }));
  });
}

ws.addEventListener("message", async (event) => {
  const msg = JSON.parse(event.data);
  if (msg.id && callbacks.has(msg.id)) {
    const cb = callbacks.get(msg.id);
    callbacks.delete(msg.id);
    cb(msg);
  } else if (msg.method === "Fetch.requestPaused") {
    const { requestId, request } = msg.params;

    // Pass through Vite dev server source files
    if (request.url.includes("/src/") || request.url.includes("/@") || request.url.includes("node_modules")) {
      send("Fetch.continueRequest", { requestId });
      return;
    }

    console.log("Intercepted API request:", request.method, request.url);

    let bodyObj = { data: [] };
    let code = 200;

    if (request.url.includes("/api/auth/me")) {
      bodyObj = {
        data: {
          id: 1,
          email: "admin@demo.local",
          full_name: "Dr. A. Sharma (IAS)",
          role: "ADMIN",
          is_active: true,
        },
      };
    } else if (request.url.includes("/api/auth/login")) {
      bodyObj = {
        data: {
          access_token: "mock-jwt-token-admin",
          user: {
            id: 1,
            email: "admin@demo.local",
            full_name: "Dr. A. Sharma (IAS)",
            role: "ADMIN",
            is_active: true,
          },
        },
      };
    } else if (request.url.includes("/api/notifications")) {
      bodyObj = { data: [], meta: { total: 0 } };
    } else if (request.url.includes("/api/dashboard")) {
      bodyObj = { data: { kpis: {}, charts: {} } };
    }

    const bodyStr = Buffer.from(JSON.stringify(bodyObj)).toString("base64");
    send("Fetch.fulfillRequest", {
      requestId,
      responseCode: code,
      responseHeaders: [
        { name: "Content-Type", value: "application/json" },
        { name: "Access-Control-Allow-Origin", value: "*" },
      ],
      body: bodyStr,
    });
  }
});

await send("Runtime.enable");
await send("Page.enable");
await send("Fetch.enable", { patterns: [{ urlPattern: "*://*/api/*" }] });

await send("Page.navigate", { url: "http://localhost:5173/login" });

// Wait for login form
for (let i = 0; i < 25; i++) {
  const hasForm = await send("Runtime.evaluate", { expression: "!!document.querySelector('form')" });
  if (hasForm.result?.result?.value) break;
  await new Promise((r) => setTimeout(r, 200));
}

console.log("Submitting login form in Chrome...");
await send("Runtime.evaluate", {
  expression: `(() => {
    const email = document.querySelector('input[type="email"]');
    const pwd = document.querySelector('input[type="password"]');
    const btn = document.querySelector('button[type="submit"]');
    email.value = 'admin@demo.local';
    email.dispatchEvent(new Event('input', { bubbles: true }));
    pwd.value = 'Demo@1234';
    pwd.dispatchEvent(new Event('input', { bubbles: true }));
    btn.click();
  })()`,
});

// Wait for navigation
let currentPath = "";
for (let i = 0; i < 30; i++) {
  const pathRes = await send("Runtime.evaluate", { expression: "window.location.pathname" });
  currentPath = pathRes.result?.result?.value;
  if (currentPath === "/") break;
  await new Promise((r) => setTimeout(r, 200));
}

console.log("Current path after login submit:", currentPath);

const headerUser = await send("Runtime.evaluate", {
  expression: "document.querySelector('header')?.innerText",
});
console.log("Header text:", headerUser.result?.result?.value);

ws.close();
chrome.kill();

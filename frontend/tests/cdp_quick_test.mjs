import { spawn } from "node:child_process";

const chrome = spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", [
  "--headless=new",
  "--remote-debugging-port=9222",
  "--user-data-dir=C:\\Users\\bhanu\\AppData\\Local\\Temp\\chrome-e2e-node",
  "--disable-gpu",
  "--no-first-run",
  "--no-default-browser-check",
]);

async function waitReady(timeout = 10000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    try {
      const res = await fetch("http://localhost:9222/json/version");
      if (res.ok) return await res.json();
    } catch {}
    await new Promise((r) => setTimeout(r, 200));
  }
  throw new Error("Chrome did not start listening on port 9222 in time");
}

const version = await waitReady();
console.log("Chrome ready:", version.Browser);

const newTabRes = await fetch("http://localhost:9222/json/new?about:blank", { method: "PUT" });
const tab = await newTabRes.json();

const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r));

let id = 1;
const callbacks = new Map();
const events = [];

ws.addEventListener("message", (event) => {
  const msg = JSON.parse(event.data);
  if (msg.id && callbacks.has(msg.id)) {
    const cb = callbacks.get(msg.id);
    callbacks.delete(msg.id);
    cb(msg);
  } else if (msg.method) {
    events.push(msg);
  }
});

function send(method, params = {}) {
  const reqId = id++;
  return new Promise((resolve) => {
    callbacks.set(reqId, resolve);
    ws.send(JSON.stringify({ id: reqId, method, params }));
  });
}

await send("Runtime.enable");
await send("Page.enable");

await send("Page.navigate", { url: "http://localhost:5173/login" });

// Wait until document.querySelector('input') appears (max 5s)
let ready = false;
for (let i = 0; i < 25; i++) {
  const check = await send("Runtime.evaluate", {
    expression: "document.querySelectorAll('input').length",
  });
  if (check.result?.result?.value > 0) {
    ready = true;
    break;
  }
  await new Promise((r) => setTimeout(r, 200));
}

console.log("Inputs ready?", ready);

const evalRes = await send("Runtime.evaluate", {
  expression: `(() => {
    return {
      title: document.title,
      h1: document.querySelector('h1')?.textContent,
      h2: document.querySelector('h2')?.textContent,
      inputs: Array.from(document.querySelectorAll('input')).map(i => ({
        type: i.type,
        id: i.id,
        required: i.required,
        ariaRequired: i.getAttribute('aria-required')
      })),
      button: document.querySelector('button[type="submit"]')?.textContent
    };
  })()`,
  returnByValue: true,
});

console.log("DOM Evaluation Result:", JSON.stringify(evalRes.result?.result?.value, null, 2));

ws.close();
chrome.kill();

import { spawn } from "node:child_process";
import assert from "node:assert/strict";

console.log("==================================================");
console.log("NLAMP PHASE 7: PROPOSAL DETAIL MUTATIONS SUITE");
console.log("==================================================");

// 1. Spawn Chrome Headless
const chrome = spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", [
  "--headless=new",
  "--remote-debugging-port=9222",
  "--user-data-dir=C:\\Users\\bhanu\\AppData\\Local\\Temp\\chrome-phase7-proposals",
  "--disable-gpu",
  "--no-first-run",
  "--no-default-browser-check",
  "--window-size=1440,900",
]);

chrome.on("error", (err) => console.error("Chrome spawn error:", err));

async function waitReady(timeout = 10000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    try {
      const res = await fetch("http://localhost:9222/json/version");
      if (res.ok) return await res.json();
    } catch {}
    await new Promise((r) => setTimeout(r, 200));
  }
  throw new Error("Chrome failed to listen on port 9222");
}

const version = await waitReady();
console.log(`[Browser Info] Engine: ${version.Browser}`);

// 2. Open target page
const newTabRes = await fetch("http://localhost:9222/json/new?about:blank", { method: "PUT" });
const tab = await newTabRes.json();
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r));

let id = 1;
const callbacks = new Map();
const consoleLogs = [];
const mutationCalls = [];

const currentUser = {
  id: 1,
  email: "admin@demo.local",
  full_name: "Dr. A. Sharma (IAS)",
  role: "ADMIN",
  is_active: true,
};

let proposalState = {
  id: 1,
  proposal_number: "PROP-2026-001",
  project_id: 1,
  project_code: "ORR-P2",
  purpose: "Land acquisition for highway interchange",
  required_area_ha: 5.2,
  estimated_compensation_inr: 50000000,
  affected_families_count: 12,
  parcel_ids: [1, 2],
  status: "DRAFT",
  cases_created: null,
  cases_already_present: null,
};

let mutationDelayMs = 0;
let shouldFailNextMutation = false;

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
  } else if (msg.method === "Runtime.consoleAPICalled") {
    consoleLogs.push({
      type: msg.params.type,
      args: msg.params.args?.map((a) => a.value || a.description || ""),
    });
  } else if (msg.method === "Fetch.requestPaused") {
    const { requestId, request } = msg.params;

    // Pass through Vite assets
    if (
      request.url.includes("/src/") ||
      request.url.includes("/@") ||
      request.url.includes("node_modules") ||
      request.url.endsWith(".jsx") ||
      request.url.endsWith(".js") ||
      request.url.endsWith(".css") ||
      request.url.endsWith(".svg")
    ) {
      send("Fetch.continueRequest", { requestId });
      return;
    }

    let bodyObj = { data: [] };
    let code = 200;

    if (request.url.includes("/api/auth/me")) {
      bodyObj = { data: currentUser };
    } else if (request.url.includes("/api/notifications")) {
      bodyObj = { data: [], meta: { total: 0 } };
    } else if (request.url.includes("/api/proposals/1/submit")) {
      mutationCalls.push({ action: "submit", url: request.url, postData: request.postData });
      if (shouldFailNextMutation) {
        shouldFailNextMutation = false;
        code = 500;
        bodyObj = { detail: "Simulated mutation server failure" };
      } else {
        if (mutationDelayMs > 0) await new Promise((r) => setTimeout(r, mutationDelayMs));
        proposalState.status = "SUBMITTED";
        bodyObj = { data: { ...proposalState } };
      }
    } else if (request.url.includes("/api/proposals/1/verify")) {
      mutationCalls.push({ action: "verify", url: request.url, postData: request.postData });
      proposalState.status = "UNDER_VERIFICATION";
      bodyObj = { data: { ...proposalState } };
    } else if (request.url.includes("/api/proposals/1/approve")) {
      mutationCalls.push({ action: "approve", url: request.url, postData: request.postData });
      proposalState.status = "APPROVED";
      proposalState.cases_created = 2;
      proposalState.cases_already_present = 0;
      bodyObj = { data: { ...proposalState } };
    } else if (request.url.includes("/api/proposals/1/reject")) {
      mutationCalls.push({ action: "reject", url: request.url, postData: request.postData });
      proposalState.status = "REJECTED";
      bodyObj = { data: { ...proposalState } };
    } else if (request.url.includes("/api/proposals/1")) {
      bodyObj = { data: { ...proposalState } };
    } else if (request.url.includes("/api/proposals")) {
      bodyObj = { data: [{ ...proposalState }], meta: { total: 1 } };
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
await send("Network.enable");
await send("Fetch.enable", { patterns: [{ urlPattern: "*://*/api/*" }] });

async function evaluate(expression) {
  const res = await send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true,
  });
  return res.result?.result?.value;
}

async function navigate(url, waitSelector = null, timeoutMs = 6000) {
  await send("Page.navigate", { url });
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (waitSelector) {
      const exists = await evaluate(`!!document.querySelector('${waitSelector}')`);
      if (exists) {
        await new Promise((r) => setTimeout(r, 200));
        return true;
      }
    } else {
      const hasContent = await evaluate(`(document.getElementById('root')?.innerText?.trim()?.length || 0) > 0`);
      if (hasContent) {
        await new Promise((r) => setTimeout(r, 250));
        return true;
      }
    }
    await new Promise((r) => setTimeout(r, 150));
  }
  return false;
}

try {
  // Pre-seed auth session as ADMIN
  await send("Page.addScriptToEvaluateOnNewDocument", {
    source: `
      sessionStorage.setItem('nlamp_token', 'mock-jwt-token-admin');
      sessionStorage.setItem('nlamp_user', JSON.stringify(${JSON.stringify(currentUser)}));
    `,
  });

  console.log("\n[TEST 1] Initial Proposal Detail Loading & Status...");
  const loaded = await navigate("http://localhost:5173/proposals/1", "h1");
  assert.ok(loaded, "Proposal Detail page failed to load");

  const initialInfo = await evaluate(`(() => {
    const title = document.querySelector('h1')?.textContent?.trim();
    const status = document.querySelector('h1')?.closest('.flex')?.querySelector('.rounded-full')?.textContent?.trim() ||
                   document.querySelector('.rounded-full')?.textContent?.trim();
    const submitBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Submit');
    return { title, status, hasSubmitBtn: !!submitBtn, submitDisabled: submitBtn?.disabled };
  })()`);

  console.log("  Initial page info:", initialInfo);
  assert.equal(initialInfo.title, "PROP-2026-001");
  assert.equal(initialInfo.status, "DRAFT");
  assert.ok(initialInfo.hasSubmitBtn, "Submit button must be rendered for DRAFT proposal");
  assert.equal(initialInfo.submitDisabled, false, "Submit button should not be disabled initially");
  console.log("  ✔ Initial state verified: DRAFT with enabled Submit button.");

  // -------------------------------------------------------------------------
  // FAILURE RECOVERY TEST
  // -------------------------------------------------------------------------
  console.log("\n[TEST 2] API Failure Recovery on Mutation...");
  shouldFailNextMutation = true;
  await evaluate(`(() => {
    const submitBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Submit');
    submitBtn?.click();
  })()`);

  // Wait for error toast and busy state to clear
  let recoveredState = null;
  for (let i = 0; i < 20; i++) {
    recoveredState = await evaluate(`(() => {
      const status = document.querySelector('h1')?.closest('.flex')?.querySelector('.rounded-full')?.textContent?.trim() ||
                     document.querySelector('.rounded-full')?.textContent?.trim();
      const submitBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Submit');
      const errorToast = document.querySelector('[role="alert"]')?.textContent?.trim();
      return { status, isBusy: submitBtn?.getAttribute('aria-busy') === 'true', isDisabled: submitBtn?.disabled, errorToast };
    })()`);
    if (recoveredState.errorToast && !recoveredState.isBusy && !recoveredState.isDisabled) break;
    await new Promise((r) => setTimeout(r, 150));
  }

  console.log("  Failure recovery check:", recoveredState);
  assert.equal(recoveredState.status, "DRAFT", "Status must remain DRAFT on API error");
  assert.equal(recoveredState.isDisabled, false, "Submit button must re-enable after failure");
  assert.ok(recoveredState.errorToast, "Error toast must be displayed on mutation failure");
  console.log("  ✔ API failure recovery verified: error toasted, busy cleared, button re-enabled.");

  // -------------------------------------------------------------------------
  // BUSY STATE & DUPLICATE SUBMIT PROTECTION
  // -------------------------------------------------------------------------
  console.log("\n[TEST 3] Busy State & Duplicate Submit Protection...");
  mutationDelayMs = 400; // Keep in flight long enough to measure
  const callsBeforeDup = mutationCalls.length;

  const busyTriggerRes = await evaluate(`(async () => {
    const submitBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Submit');
    submitBtn?.click();
    // Wait for React to render the busy state
    await new Promise(r => setTimeout(r, 80));
    const busyOnSecondClick = submitBtn?.disabled || submitBtn?.getAttribute('aria-busy') === 'true';
    submitBtn?.click();
    return { busyOnSecondClick };
  })()`);

  assert.ok(busyTriggerRes.busyOnSecondClick, "Button must be disabled/aria-busy while mutation is in-flight");

  // Wait for mutation to complete
  for (let i = 0; i < 20; i++) {
    const isBusy = await evaluate(`(() => {
      const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Submit');
      return btn?.getAttribute('aria-busy') === 'true' || btn?.disabled;
    })()`);
    if (!isBusy) break;
    await new Promise((r) => setTimeout(r, 150));
  }
  mutationDelayMs = 0;

  const submitCalls = mutationCalls.filter(c => c.action === "submit").length - callsBeforeDup;
  assert.equal(submitCalls, 1, `Exactly 1 submit API call expected during rapid clicks, got ${submitCalls}`);
  console.log("  ✔ Busy state verified: aria-busy set, duplicate clicks discarded.");

  // -------------------------------------------------------------------------
  // SUBMIT MUTATION
  // -------------------------------------------------------------------------
  console.log("\n[TEST 4] Submit Mutation Successful Transition...");
  let afterSubmitState = null;
  for (let i = 0; i < 20; i++) {
    afterSubmitState = await evaluate(`(() => {
      const status = document.querySelector('h1')?.closest('.flex')?.querySelector('.rounded-full')?.textContent?.trim() ||
                     document.querySelector('.rounded-full')?.textContent?.trim();
      const hasVerifyBtn = Array.from(document.querySelectorAll('button')).some(b => b.textContent.trim() === 'Verify');
      return { status, hasVerifyBtn };
    })()`);
    if (afterSubmitState.status === "SUBMITTED" && afterSubmitState.hasVerifyBtn) break;
    await new Promise((r) => setTimeout(r, 150));
  }

  console.log("  After submit state:", afterSubmitState);
  assert.equal(afterSubmitState.status, "SUBMITTED", "StatusBadge must update to SUBMITTED");
  assert.ok(afterSubmitState.hasVerifyBtn, "Verify button must appear once status is SUBMITTED");
  console.log("  ✔ Submit mutation verified: status updated to SUBMITTED, Verify action exposed.");

  // -------------------------------------------------------------------------
  // VERIFY MUTATION
  // -------------------------------------------------------------------------
  console.log("\n[TEST 5] Verify Mutation Transition...");
  await evaluate(`(() => {
    const verifyBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Verify');
    verifyBtn?.click();
  })()`);

  let afterVerifyState = null;
  for (let i = 0; i < 20; i++) {
    afterVerifyState = await evaluate(`(() => {
      const status = document.querySelector('h1')?.closest('.flex')?.querySelector('.rounded-full')?.textContent?.trim() ||
                     document.querySelector('.rounded-full')?.textContent?.trim();
      const hasApproveBtn = Array.from(document.querySelectorAll('button')).some(b => b.textContent.trim() === 'Approve');
      const hasRejectBtn = Array.from(document.querySelectorAll('button')).some(b => b.textContent.trim() === 'Reject');
      return { status, hasApproveBtn, hasRejectBtn };
    })()`);
    if (afterVerifyState.status?.replace(/\s+/g, "_") === "UNDER_VERIFICATION") break;
    await new Promise((r) => setTimeout(r, 150));
  }

  console.log("  After verify state:", afterVerifyState);
  assert.equal(afterVerifyState.status?.replace(/\s+/g, "_"), "UNDER_VERIFICATION");
  assert.ok(afterVerifyState.hasApproveBtn, "Approve button must appear when UNDER_VERIFICATION");
  assert.ok(afterVerifyState.hasRejectBtn, "Reject button must appear when UNDER_VERIFICATION");
  console.log("  ✔ Verify mutation verified: status updated to UNDER_VERIFICATION, Approve/Reject exposed.");

  // -------------------------------------------------------------------------
  // REJECT REMARKS VALIDATION
  // -------------------------------------------------------------------------
  console.log("\n[TEST 6] Reject Remarks Validation in Modal...");
  // Click Reject to open modal
  await evaluate(`(() => {
    const rejectBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Reject');
    rejectBtn?.click();
  })()`);

  // Wait for modal to open
  let modalState = null;
  for (let i = 0; i < 20; i++) {
    modalState = await evaluate(`(() => {
      const modal = document.querySelector('[role="dialog"]');
      const confirmBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Confirm reject');
      return { isOpen: !!modal, hasConfirmBtn: !!confirmBtn };
    })()`);
    if (modalState.isOpen && modalState.hasConfirmBtn) break;
    await new Promise((r) => setTimeout(r, 150));
  }
  assert.ok(modalState.isOpen, "Reject modal dialog must open");

  // Ensure remarks textarea is empty
  await evaluate(`(() => {
    const ta = document.querySelector('[role="dialog"] textarea');
    if (ta) {
      ta.value = '';
      ta.dispatchEvent(new Event('input', { bubbles: true }));
      ta.dispatchEvent(new Event('change', { bubbles: true }));
    }
  })()`);

  const rejectCallsBefore = mutationCalls.filter(c => c.action === "reject").length;

  // Click Confirm reject with empty remarks
  await evaluate(`(() => {
    const confirmBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Confirm reject');
    confirmBtn?.click();
  })()`);

  // Wait for validation error to appear
  let validationError = null;
  for (let i = 0; i < 20; i++) {
    validationError = await evaluate(`(() => {
      const errEl = document.querySelector('[role="dialog"] [role="alert"]') || document.querySelector('[role="dialog"] .text-red-600');
      return errEl?.textContent?.trim();
    })()`);
    if (validationError) break;
    await new Promise((r) => setTimeout(r, 150));
  }

  console.log("  Validation error text:", validationError);
  assert.equal(validationError, "Rejection remarks are required.");

  const rejectCallsAfterInvalid = mutationCalls.filter(c => c.action === "reject").length;
  assert.equal(rejectCallsAfterInvalid, rejectCallsBefore, "No reject API call must occur when remarks are empty");
  console.log("  ✔ Reject validation verified: Rejection remarks are required alert shown, API call blocked.");

  // -------------------------------------------------------------------------
  // REJECT MUTATION
  // -------------------------------------------------------------------------
  console.log("\n[TEST 7] Reject Mutation with Valid Remarks...");
  await evaluate(`(() => {
    const ta = document.querySelector('[role="dialog"] textarea');
    if (ta) {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
      if (setter) {
        setter.call(ta, 'Incomplete environmental clearance from state authorities.');
      } else {
        ta.value = 'Incomplete environmental clearance from state authorities.';
      }
      ta.dispatchEvent(new Event('input', { bubbles: true }));
      ta.dispatchEvent(new Event('change', { bubbles: true }));
    }
    const confirmBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Confirm reject');
    confirmBtn?.click();
  })()`);

  // Wait for modal to close and status to update to REJECTED
  let afterRejectState = null;
  for (let i = 0; i < 20; i++) {
    afterRejectState = await evaluate(`(() => {
      const modal = document.querySelector('[role="dialog"]');
      const status = document.querySelector('h1')?.closest('.flex')?.querySelector('.rounded-full')?.textContent?.trim() ||
                     document.querySelector('.rounded-full')?.textContent?.trim();
      return { modalOpen: !!modal, status };
    })()`);
    if (!afterRejectState.modalOpen && afterRejectState.status === "REJECTED") break;
    await new Promise((r) => setTimeout(r, 150));
  }

  console.log("  After reject state:", afterRejectState);
  assert.equal(afterRejectState.modalOpen, false, "Modal must close on successful rejection");
  assert.equal(afterRejectState.status, "REJECTED", "Status must update to REJECTED");
  console.log("  ✔ Reject mutation verified: modal dismissed, status updated to REJECTED.");

  // -------------------------------------------------------------------------
  // APPROVE MUTATION
  // -------------------------------------------------------------------------
  console.log("\n[TEST 8] Approve Mutation Transition...");
  // Reset proposal state to UNDER_VERIFICATION to test Approve path
  proposalState.status = "UNDER_VERIFICATION";
  await navigate("http://localhost:5173/proposals/1", "h1");

  await evaluate(`(() => {
    const approveBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Approve');
    approveBtn?.click();
  })()`);

  let afterApproveState = null;
  for (let i = 0; i < 20; i++) {
    afterApproveState = await evaluate(`(() => {
      const status = document.querySelector('h1')?.closest('.flex')?.querySelector('.rounded-full')?.textContent?.trim() ||
                     document.querySelector('.rounded-full')?.textContent?.trim();
      const casesText = Array.from(document.querySelectorAll('p')).find(p => p.textContent.includes('Cases created'))?.textContent?.trim();
      return { status, casesText };
    })()`);
    if (afterApproveState.status === "APPROVED" && afterApproveState.casesText) break;
    await new Promise((r) => setTimeout(r, 150));
  }

  console.log("  After approve state:", afterApproveState);
  assert.equal(afterApproveState.status, "APPROVED");
  assert.ok(afterApproveState.casesText.includes("Cases created: 2"), "Cases created count must be displayed");
  console.log("  ✔ Approve mutation verified: status updated to APPROVED, cases created reported.");

  console.log("\n==================================================");
  console.log("PROPOSAL DETAIL MUTATIONS: ALL TESTS PASSED");
  console.log("==================================================");
} finally {
  ws.close();
  chrome.kill();
}

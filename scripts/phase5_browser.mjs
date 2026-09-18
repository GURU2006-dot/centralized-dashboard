import { chromium } from "/tmp/pw/node_modules/playwright/index.mjs";

const BASE = process.env.NLAMP_UI || "http://127.0.0.1:5173";
const PASS = process.env.NLAMP_PASS || "Demo@1234";
const results = [];

function rec(area, test, ok, notes = "") {
  results.push({ area, test, ok, notes });
  console.log(ok ? "PASS" : "FAIL", area, "—", test, notes);
}

async function visible(locator) {
  try {
    await locator.first().waitFor({ state: "visible", timeout: 15000 });
    return true;
  } catch (e) {
    return false;
  }
}

async function login(page, email) {
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  await page.getByLabel("Official email").waitFor();
  await page.getByLabel("Official email").fill(email);
  await page.getByLabel("Password").fill(PASS);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.waitForURL((url) => !url.pathname.includes("/login"), { timeout: 15000 });
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.setDefaultTimeout(20000);

  try {
    await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
    rec("Browser", "login page", await visible(page.getByRole("heading", { name: "Sign in" })));
    rec("Browser", "synthetic banner", await visible(page.getByText("synthetic demonstration data").first()));

    await page.getByLabel("Official email").fill("nobody@demo.local");
    await page.getByLabel("Password").fill("bad");
    await page.getByRole("button", { name: "Continue" }).click();
    rec("Browser", "invalid login toast", await visible(page.getByRole("status").first()));

    await login(page, "admin@demo.local");
    rec("Browser", "admin dashboard", await visible(page.getByRole("heading", { name: /command dashboard/i })));
    rec("Browser", "KPI cards", await visible(page.getByText("Total projects")));

    await page.getByRole("link", { name: "Projects" }).first().click();
    rec("Browser", "projects list", await visible(page.getByRole("heading", { name: "Projects" })));

    await page.locator("table a").first().waitFor();
    await page.locator("table a").first().click();
    rec("Browser", "project detail", await visible(page.getByText(/Overview|Land parcels/i).first()));

    await page.getByRole("link", { name: "Land Parcels" }).first().click();
    rec("Browser", "parcels", await visible(page.getByRole("heading", { name: /Land parcels/i })));

    await page.getByRole("link", { name: "GIS Map" }).first().click();
    rec("Browser", "GIS heading", await visible(page.getByRole("heading", { name: /GIS map/i })));
    rec("Browser", "leaflet canvas", await visible(page.locator(".leaflet-container").first()));

    await page.getByRole("link", { name: "Proposals" }).first().click();
    rec("Browser", "proposals", await visible(page.getByRole("heading", { name: "Proposals" })));

    await page.getByRole("link", { name: "Acquisition Cases" }).first().click();
    rec("Browser", "cases", await visible(page.getByRole("heading", { name: /Acquisition cases/i })));
    await page.locator("table a").first().waitFor();
    await page.locator("table a").first().click();
    rec("Browser", "case detail", await visible(page.getByText("Delay risk")));
    rec("Browser", "run prediction button", await visible(page.getByRole("button", { name: /Run prediction/i })));
    await page.getByRole("button", { name: /Run prediction/i }).click();
    rec(
      "Browser",
      "prediction score shown",
      (await visible(page.getByRole("status").filter({ hasText: /Delay risk score/i }))) ||
        (await visible(page.getByText("/ 100").first())),
    );

    await page.getByRole("link", { name: "Alerts" }).first().click();
    rec("Browser", "alerts", await visible(page.getByRole("heading", { name: "Alerts" })));

    await page.getByRole("link", { name: "Analytics" }).first().click();
    rec("Browser", "analytics", await visible(page.getByRole("heading", { name: "Analytics" })));

    await page.getByRole("link", { name: "Integrations" }).first().click();
    rec("Browser", "integrations MOCK", await visible(page.getByText("MOCK / DEMONSTRATION").first()));

    await page.getByRole("link", { name: "Model information" }).first().click();
    rec(
      "Browser",
      "model disclaimer",
      await visible(page.getByText("not a validated government decision-making model")),
    );

    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole("button", { name: "Open menu" }).click();
    rec("Browser", "mobile sidebar", await visible(page.getByRole("link", { name: "Dashboard" }).first()));
    await page.getByRole("link", { name: "Dashboard" }).first().click();
    await page.getByRole("button", { name: "Log out" }).click();
    rec(
      "Browser",
      "logout",
      page.url().includes("/login") || (await visible(page.getByRole("heading", { name: "Sign in" }))),
    );

    const field = await browser.newPage({ viewport: { width: 390, height: 844 } });
    await login(field, "field@demo.local");
    rec("Browser", "field login mobile", true);
    await field.getByRole("button", { name: "Open menu" }).click();
    rec("Browser", "field has no proposals nav", (await field.getByRole("link", { name: "Proposals" }).count()) === 0);
    await field.getByRole("link", { name: "Field Verification" }).click();
    rec("Browser", "field verification page", await visible(field.getByRole("heading", { name: /Field verification/i })));
    await field.close();
  } catch (err) {
    rec("Browser", "walkthrough exception", false, String(err).slice(0, 400));
  } finally {
    await browser.close();
  }

  const fails = results.filter((r) => !r.ok);
  console.log(`\nBrowser ${results.length - fails.length} passed, ${fails.length} failed of ${results.length}`);
  process.exit(fails.length ? 1 : 0);
}

main();

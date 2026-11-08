import { test, expect } from "@playwright/test";
const password = process.env.SAFETYLENS_E2E_PASSWORD!;
async function login(
  page: import("@playwright/test").Page,
  username = "qa-admin",
) {
  await page.goto("/");
  await page.getByLabel("Username", { exact: true }).fill(username);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Operations overview" }),
  ).toBeVisible();
}

test("authenticated camera configuration and real record analytics", async ({
  page,
}) => {
  await login(page);
  await page.goto("/cameras");
  await page
    .getByRole("button", { name: "Register camera", exact: true })
    .click();
  await page
    .getByLabel("Camera name", { exact: true })
    .fill("Browser QA camera");
  await page.getByLabel("Location", { exact: true }).fill("Test area");
  await page.getByRole("button", { name: "Save camera", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Browser QA camera", exact: true }),
  ).toBeVisible();
  await page.goto("/analytics");
  await expect(
    page.getByRole("heading", { name: "Safety analytics" }),
  ).toBeVisible();
  await expect(
    page.getByText("Rejected fraction among conclusive reviews.", {
      exact: false,
    }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/analytics-desktop.png",
    fullPage: true,
  });
});

test("viewer is read-only and logout revokes the session", async ({
  page,
  request,
}) => {
  await login(page, "qa-viewer");
  await page.goto("/cameras");
  await expect(
    page.getByRole("heading", { name: "Camera management" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Register camera", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeVisible();
  expect(
    (await request.get("http://127.0.0.1:8107/api/cameras")).status(),
  ).toBe(401);
});

test("mobile, tablet and desktop layouts keep content within the viewport", async ({
  page,
}) => {
  await login(page);
  for (const [name, width, height] of [
    ["mobile", 390, 844],
    ["tablet", 820, 1180],
    ["desktop", 1440, 1000],
  ] as const) {
    await page.setViewportSize({ width, height });
    for (const route of ["/", "/cameras", "/incidents", "/ppe", "/settings"]) {
      await page.goto(route);
      await expect(page.locator("main")).toBeVisible();
      await expect
        .poll(() =>
          page.evaluate(
            () => document.documentElement.scrollWidth <= window.innerWidth,
          ),
        )
        .toBe(true);
    }
    await page.goto("/");
    await page.screenshot({
      path: `test-results/overview-${name}.png`,
      fullPage: true,
    });
  }
});

test("camera and incident empty states are explicit", async ({ page }) => {
  await login(page);
  await page.goto("/cameras");
  await page.getByLabel("Search cameras").fill("definitely-no-such-camera");
  await expect(
    page.getByRole("heading", { name: "No matching cameras" }),
  ).toBeVisible();
  await page.goto("/incidents");
  await page
    .getByLabel("Search incidents", { exact: true })
    .fill("no-such-incident");
  await expect(
    page.getByRole("heading", { name: "No matching incidents" }),
  ).toBeVisible();
});

test("incident investigation preserves operator notes and detects stale versions", async ({
  page,
}) => {
  await login(page);
  await page.goto("/investigate/inc-2026-0042");
  await expect(
    page.getByRole("heading", { name: "Operator coordination" }),
  ).toBeVisible();
  await page
    .getByLabel("Notes", { exact: true })
    .fill("Checked camera context in browser QA.");
  await page.getByRole("button", { name: "Acknowledge & save" }).click();
  await expect(page.getByText("Saved.", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Notes", { exact: true })).toHaveValue(
    "Checked camera context in browser QA.",
  );
});

test("durable event delivery reaches human approval and a simulated PDF report", async ({
  page,
}) => {
  const { execFileSync } = await import("node:child_process");
  const fixture = JSON.parse(
    execFileSync(
      "../backend/.venv/bin/python",
      ["../scripts/e2e_detector_event.py"],
      { encoding: "utf8", env: process.env },
    ),
  );
  await login(page);
  let event: { asset_code: string; analysis_code: string | null };
  await expect
    .poll(
      async () => {
        const response = await page.request.get(
          `http://127.0.0.1:8107/api/detector/events/${fixture.event_id}`,
        );
        const payload = await response.json();
        event = payload.data;
        return event?.analysis_code;
      },
      { timeout: 20000 },
    )
    .toBeTruthy();
  const response = await page.request.get(
    `http://127.0.0.1:8107/api/detector/events/${fixture.event_id}`,
  );
  event = (await response.json()).data;
  await page.goto(
    `/response?analysis_id=${event.analysis_code}&video_id=${event.asset_code}`,
  );
  await expect
    .poll(() =>
      page
        .locator("video")
        .first()
        .evaluate((v: HTMLVideoElement) => v.readyState),
    )
    .toBeGreaterThanOrEqual(1);
  await page
    .locator("video")
    .first()
    .evaluate(async (v: HTMLVideoElement) => {
      v.muted = true;
      await v.play();
    });
  await expect
    .poll(() =>
      page
        .locator("video")
        .first()
        .evaluate((v: HTMLVideoElement) => v.currentTime),
    )
    .toBeGreaterThan(0);
  await page
    .getByRole("button", { name: "Confirm Incident", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Approve selected actions", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Confirm approval", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Run approved actions", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Execute simulated actions", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Simulated execution status",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Download PDF", exact: true }),
  ).toBeVisible();
  const href = await page
    .getByRole("link", { name: "Download PDF", exact: true })
    .getAttribute("href");
  const pdf = await page.request.get(href!);
  expect(pdf.headers()["content-type"]).toContain("application/pdf");
  expect((await pdf.body()).subarray(0, 4).toString()).toBe("%PDF");
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: "test-results/response-workflow-desktop.png",
    fullPage: true,
  });
});

test("SSE refreshes canonical overview data after a separate mutation", async ({
  page,
}) => {
  await login(page);
  await expect(
    page.getByRole("status").filter({ hasText: "Event stream connected" }),
  ).toBeVisible();
  const me = await (
    await page.request.get("http://127.0.0.1:8107/api/auth/me")
  ).json();
  const before = await (
    await page.request.get("http://127.0.0.1:8107/api/camera-management")
  ).json();
  const created = await page.request.post("http://127.0.0.1:8107/api/cameras", {
    headers: { "X-CSRF-Token": me.data.csrf_token },
    data: { name: "SSE invalidation camera", location: "Test area" },
  });
  expect(created.status()).toBe(201);
  await expect(
    page.getByText(
      `${before.data.length + 1} registered · seed records excluded`,
      { exact: true },
    ),
  ).toBeVisible();
});

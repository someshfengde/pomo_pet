import { expect, test } from "@playwright/test";

async function completeOnboarding(page) {
  await page.goto("/");
  if (await page.locator("#onboardingOverlay").isVisible()) {
    await page.getByRole("button", { name: "Start setup" }).click();
    await expect(page.locator("#onboardingOverlay")).toBeHidden();
  }
}

test("runs the timer and persists settings locally", async ({ page }) => {
  await completeOnboarding(page);

  await expect(page.getByRole("heading", { name: "Pomo Pet" })).toBeVisible();
  await expect(page.locator("#timerText")).toHaveText("25:00");
  await expect(page).toHaveTitle("Pomo Pet - Work ready");
  await expect(page.getByRole("link", { name: "Browse gallery" })).toHaveAttribute("href", "https://codex-pets.net/");
  await expect(page.locator("#weekChart .week-bar")).toHaveCount(7);
  await expect(page.locator("#insightBestDay")).toHaveText("none yet");
  await expect(page.locator("#insightEnergy")).toHaveText("unrated");
  await expect(page.locator("#insightMomentum")).not.toBeEmpty();
  await expect(page.locator("#totalFocus")).toHaveText("0m");
  await expect(page.locator("#petLevel")).toHaveText("Level 1");
  await expect(page.locator("#petXp")).toHaveText("0 XP");
  await expect(page.locator("#goalPercent")).toHaveText("0%");
  await expect(page.locator("#achievementList .achievement-item")).toHaveCount(4);
  await expect(page.getByRole("button", { name: "Share" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Import" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Export" })).toBeVisible();
  await expect(page.locator("#installStatus")).not.toBeEmpty();
  await expect(page.locator("#cacheStatus")).not.toBeEmpty();
  await expect(page.locator("#storageStatus")).not.toBeEmpty();
  await expect(page.locator("#wakeLockToggle")).toBeVisible();
  await expect(page.locator("#breakPrompt")).toContainText(/Look|Stand|Refill|Walk|Stretch|Open/);
  await expect(page.locator("#sessionReviewOverlay")).toBeHidden();
  const firstBreakPrompt = await page.locator("#breakPrompt").textContent();
  await page.getByRole("button", { name: "Next" }).click();
  await expect(page.locator("#breakPrompt")).not.toHaveText(firstBreakPrompt || "");

  await page.locator("#workInput").fill("1");
  await page.locator("#dailyGoalInput").fill("15");
  await page.locator("#intentionInput").fill("Ship the PWA");
  await expect(page.locator("#timerText")).toHaveText("01:00");

  await page.locator("#startPauseButton").click();
  await expect(page.getByRole("button", { name: "Pause" })).toBeVisible();
  await expect(page).toHaveTitle(/Work - Pomo Pet/);
  await expect(page.locator("#timerText")).not.toHaveText("01:00", { timeout: 2500 });

  await page.reload();
  await expect(page.locator("#workInput")).toHaveValue("1");
  await expect(page.locator("#dailyGoalInput")).toHaveValue("15");
  await expect(page.locator("#intentionInput")).toHaveValue("Ship the PWA");
});

test("supports quick focus intention chips", async ({ page }) => {
  await completeOnboarding(page);

  await page.getByRole("button", { name: "Writing" }).click();
  await expect(page.locator("#intentionInput")).toHaveValue("Writing");
  await expect(page.getByRole("button", { name: "Writing" })).toHaveAttribute("aria-pressed", "true");
});

test("integrates local task list with focus sessions", async ({ page }) => {
  await completeOnboarding(page);

  await expect(page.locator("#taskSummary")).toHaveText("0 open");
  await page.locator("#taskInput").fill("Write launch checklist");
  await page.getByRole("button", { name: "Add" }).click();

  await expect(page.locator("#taskSummary")).toHaveText("1 open");
  await expect(page.locator("#taskList")).toContainText("Write launch checklist");
  await expect(page.locator("#intentionInput")).toHaveValue("Write launch checklist");
  await expect(page.locator('.task-item[data-active="true"]')).toContainText("Write launch checklist");

  await page.locator("#workInput").fill("1");
  await page.evaluate(() => {
    const stored = JSON.parse(localStorage.getItem("pomo-pet.web.v1"));
    stored.timer.remaining = 1;
    localStorage.setItem("pomo-pet.web.v1", JSON.stringify(stored));
  });
  await page.reload();
  await page.locator("#startPauseButton").click();
  await expect(page.locator("#sessionReviewOverlay")).toBeVisible({ timeout: 3000 });
  await page.locator("#skipReviewButton").click();
  await expect(page.locator("#taskList")).toContainText("1m focused");

  await page.getByLabel("Complete Write launch checklist").check();
  await expect(page.locator("#taskSummary")).toHaveText("0 open");
  await expect(page.locator('.task-item[data-completed="true"]')).toContainText("Write launch checklist");
});

test("supports custom pet spritesheets", async ({ page }) => {
  await completeOnboarding(page);

  await expect(page.locator("#petGallery .pet-choice")).toHaveCount(4);
  await page.getByRole("button", { name: /Blueberry/ }).click();
  await expect(page.locator("#petSprite")).toHaveAttribute("aria-label", "Animated blueberry pet");
  await expect(page.locator("#petSprite")).toHaveCSS("height", "208px");
  await expect(page.locator("#petSprite")).toHaveCSS("background-size", "1536px");
  expect(await page.locator("#petSprite").evaluate((element) => element.style.getPropertyValue("--pet-frames"))).toBe("1");

  await page.locator("#customPetInput").fill("https://example.com/pet.webp");

  await expect(page.locator("#petSprite")).toHaveAttribute("aria-label", "Animated custom pet");
  const backgroundImage = await page.locator("#petSprite").evaluate((element) => getComputedStyle(element).backgroundImage);
  expect(backgroundImage).toContain("https://example.com/pet.webp");
});

test("resolves Codex Pets share links", async ({ page, context }) => {
  await context.route("**/api/pets/clipops", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        pet: {
          id: "clipops",
          displayName: "ClipOps",
          spritesheetUrl: "https://codex-pets.net/assets/pets/v/1780497804791/clipops/spritesheet.webp",
          validationReport: {
            atlasSize: "1536x1872",
            cellSize: "192x208",
          },
        },
      }),
      headers: { "access-control-allow-origin": "*" },
    });
  });

  await completeOnboarding(page);
  await page.locator("#customPetInput").fill("https://codex-pets.net/share/clipops");

  await expect(page.locator("#customPetStatus")).toHaveText("Loaded ClipOps.");
  await expect.poll(
    () => page.locator("#petSprite").evaluate((element) => getComputedStyle(element).backgroundImage),
  ).toContain("https://codex-pets.net/assets/pets/v/1780497804791/clipops/spritesheet.webp");
  await expect(page.locator("#petSprite")).toHaveCSS("height", "208px");
});

test("resolves Codex Pets pet pages with manifest sizing", async ({ page, context }) => {
  await context.route("**/api/pets/dario", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        pet: {
          id: "dario",
          displayName: "Dario",
          spritesheetUrl: "https://codex-pets.net/assets/pets/v/1777693574152/dario/spritesheet.webp",
          validationReport: {
            atlasSize: "1536x1872",
            cellSize: "192x208",
          },
        },
      }),
      headers: { "access-control-allow-origin": "*" },
    });
  });
  await context.route("**/assets/pets/v/1777693574152/dario/pet.json", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        id: "dario",
        displayName: "Dario",
        spritesheetPath: "spritesheet.webp",
      }),
      headers: { "access-control-allow-origin": "*" },
    });
  });

  await completeOnboarding(page);
  await page.locator("#customPetInput").fill("https://codex-pets.net/pets/dario");

  await expect(page.locator("#customPetStatus")).toHaveText("Loaded Dario.");
  const sprite = page.locator("#petSprite");
  await expect(sprite).toHaveCSS("width", "192px");
  await expect(sprite).toHaveCSS("height", "208px");
  await expect(sprite).toHaveCSS("background-size", "1536px");
  await expect(sprite).toHaveAttribute("aria-label", "Animated custom pet");
});

test("captures post-session reflections locally", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("pomo-pet.web.v1", JSON.stringify({
      settings: {
        preset: "classic",
        work: 1,
        break: 1,
        longBreak: 1,
        interval: 0,
        notifications: false,
        tick: false,
        wakeLock: false,
        pet: "avocado",
        customPetUrl: "",
        dailyGoalMinutes: 15,
        currentIntention: "Write launch notes",
        breakPromptIndex: 0,
        onboarded: true,
      },
      timer: {
        phase: "work",
        remaining: 1,
        running: false,
        sessionsCompleted: 0,
        message: "Ready.",
      },
      stats: { sessions: [], bestStreak: 0 },
    }));
  });

  await page.goto("/");
  await expect(page.locator("#timerText")).toHaveText("00:01");
  await page.locator("#startPauseButton").click();
  await expect(page.locator("#sessionReviewOverlay")).toBeVisible({ timeout: 3000 });

  await page.locator("#sessionReviewInput").fill("Finished the launch copy.");
  await page.locator('.review-rating button[data-energy="4"]').click();
  await page.getByRole("button", { name: "Save note" }).click();

  await expect(page.locator("#sessionReviewOverlay")).toBeHidden();
  await expect(page.locator("#todaySessions")).toHaveText("1");
  await expect(page.locator("#historyList")).toContainText("4/5 energy");
  await expect(page.locator("#historyList")).toContainText("Finished the launch copy.");
  await expect(page.locator("#insightEnergy")).toHaveText("4/5");
  await expect(page.locator("#insightBestDay")).toContainText("1m");
});

test("exposes installable PWA metadata and service worker", async ({ page, context }) => {
  await completeOnboarding(page);

  const manifest = await page.locator('link[rel="manifest"]').getAttribute("href");
  expect(manifest).toBe("./manifest.webmanifest");
  await expect(page.locator('script[src="./app.js?v=17"]')).toHaveCount(1);

  const registrationScope = await page.evaluate(async () => {
    const registration = await navigator.serviceWorker.ready;
    return registration.scope;
  });
  expect(registrationScope).toContain("127.0.0.1:4173");

  const cacheNames = await page.evaluate(() => caches.keys());
  expect(cacheNames.some((name) => name.startsWith("pomo-pet-pwa"))).toBeTruthy();

  await context.setOffline(true);
  await page.reload();
  await expect(page.getByRole("heading", { name: "Pomo Pet" })).toBeVisible();
});

test("guides first-run setup", async ({ page }) => {
  await page.goto("/");

  await expect(page.locator("#onboardingOverlay")).toBeVisible();
  await page.locator("#onboardingIntentionInput").fill("Plan launch");
  await page.getByLabel("Starting preset").getByRole("button", { name: "Sprint" }).click();
  await page.getByRole("button", { name: "Start setup" }).click();

  await expect(page.locator("#onboardingOverlay")).toBeHidden();
  await expect(page.locator("#intentionInput")).toHaveValue("Plan launch");
  await expect(page.locator("#workInput")).toHaveValue("15");
});

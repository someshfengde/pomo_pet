import { test, expect } from '@playwright/test';

const KEY = 'pomo-pet.web.v1';
const route = (page, name) => page.locator(`[data-route-link="${name}"]`).click();
async function seed(page, data = {}) {
  await page.addInitScript(({ key, data }) => {
    if (sessionStorage.getItem('seeded')) return;
    localStorage.setItem(key, JSON.stringify({ ...data,
      settings: { onboarded: true, ...data.settings } }));
    sessionStorage.setItem('seeded', 'yes');
  }, { key: KEY, data });
  await page.goto('/');
  await expect(page.locator('#startPauseButton')).toBeEnabled();
}
async function saved(page) { return page.evaluate(key => JSON.parse(localStorage.getItem(key)), KEY); }
function session(date, minutes = 25) { return { id: date, date, focusMinutes: minutes, preset: 'classic', pet: 'Avocado' }; }

test('keeps a running deadline through reload and pauses without losing progress', async ({ page }) => {
  await page.clock.install();
  await seed(page, { settings: { work: 1 } });
  await page.locator('#startPauseButton').click();
  await page.clock.runFor(5100);
  expect(Number((await page.locator('#timerText').textContent()).split(':')[1])).toBeLessThan(60);
  const deadline = (await saved(page)).timer.deadline;
  await page.reload();
  await expect(page.locator('#startPauseButton')).toHaveText('Pause');
  expect((await saved(page)).timer.deadline).toBe(deadline);
  await page.locator('#startPauseButton').click();
  const pausedTime = await page.locator('#timerText').textContent();
  expect(Number(pausedTime.split(':')[1])).toBeLessThan(60);
  await route(page, 'settings');
  await page.locator('#tickToggle').check();
  await page.locator('#dailyGoalInput').fill('60');
  await page.locator('#dailyGoalInput').blur();
  await page.clock.runFor(5000);
  await route(page, 'focus');
  await expect(page.locator('#timerText')).toHaveText(pausedTime);
  await expect(page.locator('#startPauseButton')).toHaveText('Resume');
});

test('finishes only one overdue session and waits at the phase boundary', async ({ page }) => {
  await page.clock.install({ time: new Date('2026-09-11T10:00:00Z') });
  await seed(page, { settings: { work: 1, break: 1, interval: 0 } });
  await page.locator('#startPauseButton').click();
  const deadline = (await saved(page)).timer.deadline;
  await page.clock.fastForward(3600000);
  await expect(page.locator('#todaySessions')).toHaveText('1');
  await expect(page.locator('#phaseLabel')).toHaveText('Break');
  await expect(page.locator('#timerText')).toHaveText('01:00');
  await expect(page.locator('#sessionReviewOverlay')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('#startPauseButton')).toHaveText('Start');
  await page.reload();
  await expect(page.locator('#todaySessions')).toHaveText('1');
  expect((await saved(page)).stats.sessions[0].completedAt).toBe(new Date(deadline).toISOString());
});

test('credits the original task and duration after settings and intention change', async ({ page }) => {
  await page.clock.install();
  await seed(page, { settings: { work: 1, activeTaskId: 'a', currentIntention: 'Original' },
    stats: { tasks: [{ id: 'a', title: 'Original' }, { id: 'b', title: 'Next' }], sessions: [] } });
  await page.locator('#startPauseButton').click();
  await route(page, 'settings');
  await page.locator('#workInput').fill('30');
  await page.locator('#workInput').blur();
  await route(page, 'tasks');
  await page.getByRole('button', { name: 'Next Ready for focus' }).click();
  await page.clock.runFor(60100);
  const data = await saved(page);
  expect(data.stats.sessions).toHaveLength(1);
  expect(data.stats.sessions[0]).toMatchObject({ focusMinutes: 1, intention: 'Original', taskId: 'a' });
  expect(data.stats.tasks.find(t => t.id === 'a').focusMinutes).toBe(1);
  expect(data.stats.tasks.find(t => t.id === 'b').focusMinutes).toBe(0);
});

test('typing and keyboard focus survive clock ticks', async ({ page }) => {
  await page.clock.install();
  await seed(page);
  await page.locator('#startPauseButton').click();
  await page.locator('#intentionInput').pressSequentially('Write a thoughtful note');
  await expect(page.locator('#intentionInput')).toHaveValue('Write a thoughtful note');
  await route(page, 'tasks');
  await page.locator('#taskInput').fill('Keep my draft');
  await page.clock.runFor(5100);
  await expect(page.locator('#taskInput')).toBeFocused();
  await expect(page.locator('#taskInput')).toHaveValue('Keep my draft');
  await route(page, 'settings');
  await page.locator('#workInput').fill('');
  await page.locator('#workInput').pressSequentially('42');
  await page.clock.runFor(1100);
  await expect(page.locator('#workInput')).toHaveValue('42');
  await page.locator('#workInput').blur();
  expect((await saved(page)).settings.work).toBe(42);
});

test('uses local dates and keeps yesterday’s streak alive', async ({ browser }) => {
  const context = await browser.newContext({ timezoneId: 'Asia/Kolkata' });
  const page = await context.newPage();
  await page.clock.install({ time: new Date('2026-09-10T19:00:00Z') });
  await seed(page, { stats: { sessions: [session('2026-09-09'), session('2026-09-10')] } });
  await expect(page.locator('#todaySessions')).toHaveText('0');
  await expect(page.locator('#streakCount')).toHaveText('2');
  await context.close();
});

test('recovers malformed saved state without crashing', async ({ page }) => {
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await seed(page, { settings: { work: -200, interval: Infinity, customPetMeta: { animations: { idle: null } } },
    timer: { phase: 'invalid', remaining: -12 }, stats: { sessions: 'bad', tasks: null } });
  await expect(page.locator('#timerText')).toHaveText('01:00');
  await page.locator('#startPauseButton').click();
  await expect(page.locator('#phaseLabel')).toHaveText('Work');
  expect(errors).toEqual([]);
});

test('rejects unrelated JSON without erasing history', async ({ page }) => {
  await seed(page, { stats: { sessions: [session('2026-09-11')] } });
  await route(page, 'stats');
  await page.locator('#importStatsInput').setInputFiles({ name: 'bad.json', mimeType: 'application/json', buffer: Buffer.from('{"hello":"world"}') });
  await expect(page.locator('#dataStatus')).toContainText('Import failed');
  expect((await saved(page)).stats.sessions).toHaveLength(1);
});

test('can cancel clear and import, then import a valid backup', async ({ page }) => {
  await seed(page, { stats: { sessions: [session('2026-09-11')] } });
  await route(page, 'stats');
  page.once('dialog', dialog => dialog.dismiss());
  await page.locator('#clearStatsButton').click();
  expect((await saved(page)).stats.sessions).toHaveLength(1);
  const file = { name: 'backup.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify({ stats: { sessions: [session('2026-09-10', 15)], tasks: [{ title: 'Imported task' }] }, settings: { work: -10 } })) };
  const canceled = new Promise(resolve => page.once('dialog', async dialog => {
    await dialog.dismiss();
    resolve();
  }));
  await page.locator('#importStatsInput').setInputFiles(file);
  await canceled;
  await expect(page.locator('#importStatsInput')).toHaveValue('');
  expect((await saved(page)).stats.sessions[0].focusMinutes).toBe(25);
  page.once('dialog', dialog => dialog.accept());
  await page.locator('#importStatsInput').setInputFiles(file);
  await expect(page.locator('#dataStatus')).toHaveText('Imported 1 sessions.');
  expect((await saved(page)).settings.work).toBe(1);
  await route(page, 'tasks');
  await expect(page.locator('#taskList')).toContainText('Imported task');
});

test('adding a task never discards an older task', async ({ page }) => {
  await seed(page, { stats: { sessions: [], tasks: Array.from({ length: 30 }, (_, i) => ({ id: String(i), title: `Task ${i}` })) } });
  await route(page, 'tasks');
  await page.locator('#taskInput').fill('Task 31');
  await page.getByRole('button', { name: 'Add', exact: true }).click();
  await expect(page.locator('#taskSummary')).toHaveText('31 open');
  expect((await saved(page)).stats.tasks).toHaveLength(31);
});

test('secondary tabs stay read-only and take over when the editing tab closes', async ({ page, context }) => {
  await seed(page);
  await page.locator('#startPauseButton').click();
  const other = await context.newPage();
  await other.goto('/');
  await expect(other.locator('#startPauseButton')).toBeDisabled();
  await expect(other.locator('#storageNotice')).toContainText('another tab');
  await route(other, 'stats');
  await expect(other.locator('[data-route="stats"]')).toBeVisible();
  await page.close();
  await route(other, 'focus');
  await expect(other.locator('#startPauseButton')).toBeEnabled();
  await expect(other.locator('#startPauseButton')).toHaveText('Pause');
});

test('first-run dialog traps keyboard focus and returns to the workspace', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#onboardingStartButton')).toBeEnabled();
  await page.locator('#onboardingStartButton').focus();
  await page.keyboard.press('Tab');
  await expect(page.locator('#onboardingIntentionInput')).toBeFocused();
  await page.keyboard.press('Shift+Tab');
  await expect(page.locator('#onboardingStartButton')).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#onboardingOverlay')).toBeHidden();
  expect(await page.locator('.app-shell').evaluate(el => el.inert)).toBe(false);
});

test('service worker preserves unrelated caches', async ({ page }) => {
  await page.addInitScript(async () => { await caches.open('another-app-cache'); });
  await seed(page);
  await page.evaluate(() => navigator.serviceWorker.ready);
  expect(await page.evaluate(() => caches.keys())).toContain('another-app-cache');
});

for (const size of [{ width: 390, height: 844 }, { width: 320, height: 568 }, { width: 1280, height: 720 }, { width: 1024, height: 600 }]) {
  test(`all routes fit and controls remain reachable at ${size.width}x${size.height}`, async ({ page }) => {
    await page.setViewportSize(size);
    await seed(page);
    if (size.width <= 390) {
      const button = await page.locator('#startPauseButton').boundingBox();
      expect(button.y + button.height).toBeLessThan(size.height);
    }
    for (const name of ['focus', 'tasks', 'pets', 'stats', 'settings']) {
      await route(page, name);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
      await expect(page.locator(`[data-route="${name}"]`)).toBeVisible();
    }
    await page.locator('#workInput').fill('45');
    await page.locator('#workInput').blur();
    expect((await saved(page)).settings.work).toBe(45);
  });
}

test('storage failures keep the app usable and explicitly flag unsaved work', async ({ page }) => {
  await page.addInitScript(() => {
    Storage.prototype.setItem = function () { throw new DOMException('Full', 'QuotaExceededError'); };
  });
  await page.goto('/');
  await page.locator('#onboardingStartButton').click();
  await expect(page.locator('#storageNotice')).toContainText('could not be saved');
  await page.locator('#startPauseButton').click();
  await expect(page.locator('#startPauseButton')).toHaveText('Pause');
});

test.describe('pet request races', () => {
test.use({ serviceWorkers: 'block' });
test('an older pet response cannot override a newer bundled selection', async ({ page, context }) => {
  let finish;
  const pending = new Promise(resolve => { finish = resolve; });
  let requested;
  const started = new Promise(resolve => { requested = resolve; });
  await context.route('**/api/pets/slowpet', async route => {
    requested();
    await pending;
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ id: 'slowpet', displayName: 'Slowpet' }), headers: { 'access-control-allow-origin': '*' } });
  });
  await seed(page);
  await route(page, 'pets');
  await page.locator('#customPetInput').fill('https://codex-pets.net/pets/slowpet');
  await started;
  await page.getByRole('button', { name: /Blueberry/ }).click();
  finish();
  await expect(page.locator('#customPetInput')).toHaveValue('');
  await route(page, 'focus');
  await expect(page.locator('#petSprite')).toHaveAttribute('aria-label', 'Animated blueberry pet');
});

});

test('downloaded backups include tasks and completed session records', async ({ page }) => {
  await seed(page, { stats: { sessions: [session('2026-09-11')], tasks: [{ id: 't', title: 'Keep this' }] } });
  await route(page, 'stats');
  const downloadPromise = page.waitForEvent('download');
  await page.locator('#exportStatsButton').click();
  const download = await downloadPromise;
  const stream = await download.createReadStream();
  const chunks = [];
  for await (const chunk of stream) chunks.push(chunk);
  const backup = JSON.parse(Buffer.concat(chunks).toString());
  expect(backup.stats.sessions).toHaveLength(1);
  expect(backup.stats.tasks[0].title).toBe('Keep this');
});

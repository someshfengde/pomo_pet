import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('onboarding and every workspace route pass automated accessibility checks', async ({ page }) => {
  test.setTimeout(120000);
  await page.goto('/');
  await expect(page.locator('#onboardingStartButton')).toBeEnabled();
  const audit = async () => {
    const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    expect(results.violations.map(({ id, nodes }) => ({ id, targets: nodes.map(node => node.target) }))).toEqual([]);
  };
  await audit();
  await page.locator('#onboardingStartButton').click();
  for (const route of ['focus', 'tasks', 'pets', 'stats', 'settings']) {
    await page.locator(`[data-route-link="${route}"]`).click();
    await expect(page.locator(`[data-route="${route}"]`)).toBeVisible();
    // Finish finite route transitions before measuring contrast.
    await page.locator(`[data-route="${route}"]`).evaluate(async element => {
      await Promise.all(element.getAnimations().map(animation => animation.finished));
    });
    await audit();
  }
});

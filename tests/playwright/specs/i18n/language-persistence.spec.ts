import { expect, test } from '@playwright/test';

test.describe('Language Persistence', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/aap_auth/settings/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          name: 'AAP',
          url: 'https://example.com/o/authorize',
          client_id: 'test_id',
          scope: 'read',
          approval_prompt: 'auto',
          response_type: 'code',
        }),
      });
    });
    await page.route('**/api/v1/users/me/', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          first_name: 'Test',
          last_name: 'User',
          email: 'test@example.com',
          is_superuser: true,
          is_platform_auditor: false,
        }),
      });
    });

    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('should persist language across sessions', async ({ page }) => {
    const languageSwitcher = page.locator('button[aria-label*="Select Language"], button:has-text("Select Language")').first();
    await languageSwitcher.click();
    await page.waitForTimeout(500);

    const spanishOption = page.locator('text=Español').first();
    await spanishOption.click();
    await page.waitForTimeout(1000);

    let htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('es');

    const storedPreference = await page.evaluate(() => {
      const stored = localStorage.getItem('automation-dashboard-i18n');
      return stored ? JSON.parse(stored) : null;
    });

    expect(storedPreference).toBeTruthy();
    expect(storedPreference.language).toBe('es');
    expect(storedPreference.isManualSelection).toBe(true);

    await page.reload();
    await page.waitForTimeout(1000);

    htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('es');
  });

  test('should have manual selection take precedence over browser detection', async ({ page, context }) => {
    await context.addInitScript(() => {
      Object.defineProperty(navigator, 'languages', {
        get: () => ['fr'],
      });
      Object.defineProperty(navigator, 'language', {
        get: () => 'fr',
      });
    });

    await page.goto('/');
    await page.waitForTimeout(1000);

    let htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('fr');

    const languageSwitcher = page.locator('button[aria-label*="Select Language"], button:has-text("Select Language")').first();
    await languageSwitcher.click();
    await page.waitForTimeout(500);

    const germanOption = page.locator('text=Deutsch').first();
    await germanOption.click();
    await page.waitForTimeout(1000);

    htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('de');

    await page.reload();
    await page.waitForTimeout(1000);

    htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('de');
  });

  test('should run auto-detection after clearing storage', async ({ page }) => {
    const languageSwitcher = page.locator('button[aria-label*="Select Language"], button:has-text("Select Language")').first();
    await languageSwitcher.click();
    await page.waitForTimeout(500);

    const japaneseOption = page.locator('text=日本語').first();
    await japaneseOption.click();
    await page.waitForTimeout(1000);

    let htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('ja');

    await page.evaluate(() => localStorage.clear());

    await page.reload();
    await page.waitForTimeout(1000);

    htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('en');
  });

  test('should handle localStorage unavailable (session-only persistence)', async ({ page }) => {
    await page.addInitScript(() => {
      Storage.prototype.setItem = function () {
        throw new Error('localStorage is not available');
      };
    });

    await page.goto('/');
    await page.waitForTimeout(1000);

    const languageSwitcher = page.locator('button[aria-label*="Select Language"], button:has-text("Select Language")').first();
    await languageSwitcher.click();
    await page.waitForTimeout(500);

    const spanishOption = page.locator('text=Español').first();
    await spanishOption.click();
    await page.waitForTimeout(1000);

    let htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('es');

    await page.reload();
    await page.waitForTimeout(1000);

    htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('en');
  });

  test('should track isManualSelection flag correctly', async ({ page }) => {
    const languageSwitcher = page.locator('button[aria-label*="Select Language"], button:has-text("Select Language")').first();
    await languageSwitcher.click();
    await page.waitForTimeout(500);

    const chineseOption = page.locator('text=中文').first();
    await chineseOption.click();
    await page.waitForTimeout(1000);

    const storedPreference = await page.evaluate(() => {
      const stored = localStorage.getItem('automation-dashboard-i18n');
      return stored ? JSON.parse(stored) : null;
    });

    expect(storedPreference.isManualSelection).toBe(true);
    expect(storedPreference.timestamp).toBeTruthy();
    expect(typeof storedPreference.timestamp).toBe('number');
  });
});

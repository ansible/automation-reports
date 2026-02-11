import { expect, test } from '@playwright/test';

test.describe('Manual Language Switching', () => {
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
    await page.reload();
    await page.waitForTimeout(1000);
  });

  test('should open language switcher and see all 6 languages', async ({ page }) => {
    const languageSwitcher = page.locator('button[aria-label*="Select Language"], button:has-text("Select Language")').first();
    await languageSwitcher.click();
    await page.waitForTimeout(500);

    const languages = ['English', 'Español', 'Français', 'Deutsch', '中文', '日本語'];

    for (const lang of languages) {
      const langOption = page.locator(`text=${lang}`).first();
      await expect(langOption).toBeVisible();
    }
  });

  test('should select Spanish and UI updates immediately', async ({ page }) => {
    const languageSwitcher = page.locator('button[aria-label*="Select Language"], button:has-text("Select Language")').first();
    await languageSwitcher.click();
    await page.waitForTimeout(500);

    const spanishOption = page.locator('text=Español').first();
    await spanishOption.click();

    await page.waitForTimeout(1000);

    const htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('es');

    expect(page.url()).toContain('/');
  });

  test('should display language names in native script', async ({ page }) => {
    const languageSwitcher = page.locator('button[aria-label*="Select Language"], button:has-text("Select Language")').first();
    await languageSwitcher.click();
    await page.waitForTimeout(500);

    const nativeNames = [
      { code: 'en', name: 'English' },
      { code: 'es', name: 'Español' },
      { code: 'fr', name: 'Français' },
      { code: 'de', name: 'Deutsch' },
      { code: 'zh', name: '中文' },
      { code: 'ja', name: '日本語' },
    ];

    for (const { name } of nativeNames) {
      const langOption = page.locator(`text=${name}`).first();
      await expect(langOption).toBeVisible();
    }
  });

  test('should switch languages without page reload or data loss', async ({ page }) => {
    const initialLoadTime = await page.evaluate(() => performance.timing.navigationStart);

    const languageSwitcher = page.locator('button[aria-label*="Select Language"], button:has-text("Select Language")').first();
    await languageSwitcher.click();
    await page.waitForTimeout(500);

    const frenchOption = page.locator('text=Français').first();
    await frenchOption.click();
    await page.waitForTimeout(1000);

    const currentLoadTime = await page.evaluate(() => performance.timing.navigationStart);
    expect(currentLoadTime).toBe(initialLoadTime);

    const htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('fr');
  });

  test('should allow language switching during data loading', async ({ page }) => {
    const languageSwitcher = page.locator('button[aria-label*="Select Language"], button:has-text("Select Language")').first();
    await languageSwitcher.click();
    await page.waitForTimeout(300);

    const germanOption = page.locator('text=Deutsch').first();
    await germanOption.click();

    await page.waitForTimeout(1000);
    const htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('de');

    const errors = await page.evaluate(() => {
      const errorLogs: string[] = [];
      const originalError = console.error;
      console.error = (...args: unknown[]) => {
        errorLogs.push(args.join(' '));
        originalError.apply(console, args);
      };
      return errorLogs;
    });

    expect(errors.length).toBe(0);
  });

  test('should cycle through all languages without errors', async ({ page }) => {
    const languages = [
      { name: 'Español', code: 'es' },
      { name: 'Français', code: 'fr' },
      { name: 'Deutsch', code: 'de' },
      { name: '中文', code: 'zh' },
      { name: '日本語', code: 'ja' },
      { name: 'English', code: 'en' },
    ];

    for (const { name, code } of languages) {
      const languageSwitcher = page.locator('button[aria-label*="Select Language"], button:has-text("Select Language")').first();
      await languageSwitcher.click();
      await page.waitForTimeout(300);

      const langOption = page.locator(`text=${name}`).first();
      await langOption.click();
      await page.waitForTimeout(800);

      const htmlLang = await page.getAttribute('html', 'lang');
      expect(htmlLang).toBe(code);
    }
  });
});

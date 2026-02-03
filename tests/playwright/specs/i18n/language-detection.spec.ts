import { expect, test } from '@playwright/test';

test.describe('Automatic Language Detection', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('should detect supported language (Spanish browser → Spanish UI)', async ({ page, context }) => {
    await context.addInitScript(() => {
      Object.defineProperty(navigator, 'languages', {
        get: () => ['es'],
      });
      Object.defineProperty(navigator, 'language', {
        get: () => 'es',
      });
    });

    await page.goto('/');
    await page.waitForTimeout(1000);

    const htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('es');
  });

  test('should fallback to English for unsupported language', async ({ page, context }) => {
    await context.addInitScript(() => {
      Object.defineProperty(navigator, 'languages', {
        get: () => ['pl'],
      });
      Object.defineProperty(navigator, 'language', {
        get: () => 'pl',
      });
    });

    await page.goto('/');
    await page.waitForTimeout(1000);

    const htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('en');
  });

  test('should use first supported language from preference list', async ({ page, context }) => {
    await context.addInitScript(() => {
      Object.defineProperty(navigator, 'languages', {
        get: () => ['pl', 'fr', 'en'],
      });
      Object.defineProperty(navigator, 'language', {
        get: () => 'pl',
      });
    });

    await page.goto('/');
    await page.waitForTimeout(1000);

    const htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('fr');
  });

  test('should match regional variant to base language (en-GB → en)', async ({ page, context }) => {
    await context.addInitScript(() => {
      Object.defineProperty(navigator, 'languages', {
        get: () => ['en-GB'],
      });
      Object.defineProperty(navigator, 'language', {
        get: () => 'en-GB',
      });
    });

    await page.goto('/');
    await page.waitForTimeout(1000);

    const htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('en');
  });

  test('should detect and validate all supported languages', async ({ browser }) => {
    const supportedLanguages = ['en', 'es', 'fr', 'de', 'zh', 'ja'];

    for (const lang of supportedLanguages) {
      const context = await browser.newContext({ locale: lang });
      const page = await context.newPage();

      await page.goto('/');

      await page.waitForFunction((expectedLang) =>
        document.documentElement.getAttribute('lang') === expectedLang,
        lang,
        { timeout: 5000 }
      );

      const htmlLang = await page.getAttribute('html', 'lang');
      expect(htmlLang).toBe(lang);

      await context.close();
    }
  });
});

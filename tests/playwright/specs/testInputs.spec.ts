import { test, expect, Page } from '@playwright/test';
import { mockReportRoute, mockReportDetailsRoute } from '../support/interceptors.ts';
import { loginUser } from '../support/helpers.ts';
import reportDetails from '../fixtures/reportDetails.json' assert { type: 'json' };
import templateOptions from '../fixtures/templateOptions.json' assert { type: 'json' };
import templates from '../fixtures/templates.json' assert { type: 'json' };
import organizations from '../fixtures/organizations.json' assert { type: 'json' };
import projects from '../fixtures/projects.json' assert { type: 'json' };
import labels from '../fixtures/labels.json' assert { type: 'json' };
import reportResponseByTemplate from '../fixtures/reportResponseByTemplate.json' assert { type: 'json' };
import reportDetailsDateRangePast6Months from '../fixtures/reportDetailsDateRangePast6Months.json' assert { type: 'json' };

test.describe('Test inputs', () => {
  test.beforeEach(async ({ page }) => {
    await loginUser(
      page,
      templateOptions,
      templates,
      organizations,
      projects,
      labels,
      { count: 0, next: null, previous: null, results: [] },
      reportDetails,
    );
    await page.goto('/');
    await mockReportRoute(page, reportResponseByTemplate, '?date_range=last_6_month&page=1&page_size=10&ordering=name');
    await mockReportDetailsRoute(page, reportDetailsDateRangePast6Months, '?date_range=last_6_month');
    await expect(page.getByText('Discover the significant cost')).toBeVisible(); //await page.getByRole('button', { name: 'Save as Report', exact: true }).click();
    await page.getByRole('button', { name: 'Month to date' }).click();
    await page.getByRole('menuitem', { name: 'Past 6 months' }).click();
  });

  test('Test report name input max length', async ({ page }) => {
    await page.getByRole('button', { name: 'Save as Report', exact: true }).click();
    const nameInput = page.locator('#name');
    await expect(nameInput).toBeVisible();
    await nameInput.fill('A'.repeat(300));
    const inputValue = await nameInput.inputValue();
    expect(inputValue.length).toBeLessThanOrEqual(255);
    expect(inputValue.length).toBeGreaterThan(0);
  });

  test('Test numerical inputs min value', async ({ page }) => {
    const numericalInputs = page.locator('input[type="number"]');
    const count = await numericalInputs.count();
    for (let i = 0; i < count; i++) {
      const input = numericalInputs.nth(i);
      const value = await input.inputValue();
      await input.fill('-10');
      await input.blur();
      await expect(page.getByText('Value must be greater then 0!')).toBeVisible();
      await input.fill(value);
      await input.blur();
    }
  });

  test('Test numerical inputs max value', async ({ page }) => {
    const maxValues = [
      { element: 'hourly-manual-costs', maxValue: 1000 },
      { element: 'hourly-automated-process-costs', maxValue: 1000 },
      { element: '0-time_taken_manually_execute_minutes', maxValue: 1000000 },
    ];
    const count = maxValues.length;
    for (let i = 0; i < count; i++) {
      const input = page.locator(`input[id="${maxValues[i].element}"]`);
      const value = await input.inputValue();
      await input.fill((maxValues[i].maxValue + 1).toString());
      await input.blur();
      await expect(page.getByText(`Value must be less than or equal to ${maxValues[i].maxValue}!`)).toBeVisible();
      await input.fill(value);
      await input.blur();
    }
  });

  test('Test numerical inputs non numeric values', async ({ page }) => {
    const numericalInputs = page.locator('input[type="number"]');
    const count = await numericalInputs.count();
    const inputTestValues = ['abc', '!@#$', 'cvxbfgdbh', ' '];
    const inputTestValuesCount = inputTestValues.length;
    for (let i = 0; i < count; i++) {
      const input = numericalInputs.nth(i);
      const value = await input.inputValue();
      for (let j = 0; j < inputTestValuesCount; j++) {
        await input.focus();
        await input.clear();
        await input.pressSequentially(inputTestValues[j]);
        await input.blur();
        await expect(page.getByText('Please enter a valid number!')).toBeVisible();
        await input.fill(value);
        await input.blur();
      }
    }
  });
});

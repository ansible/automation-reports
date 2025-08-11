import { expect, Page } from '@playwright/test';

export async function checkCardContent(
  page: Page,
  expectedValues: { label: string; value: string; }[]
) {
  for (const { label, value } of expectedValues) {
    const card = page
      .locator(".pf-v6-c-card")
      .filter({ hasText: label });
  
    const labelSpan = card.locator("span", { hasText: label });
    await expect(labelSpan).toBeVisible();
    const valueSpan = card.locator("span").filter({ hasText: value }).first();
    await expect(valueSpan).toBeVisible();
  }
}

export async function generateExpectedTotals(
  successfulJobs: string,
  failedJobs: string,
  uniqueHosts: string,
  automationHours: string
) {
  return [
    { label: "Total number of successful jobs", value: successfulJobs },
    { label: "Total number of failed jobs", value: failedJobs },
    { label: "Total number of unique hosts automated", value: uniqueHosts },
    { label: "Total hours of automation", value: automationHours },
  ];
}

export async function generateCostAndSavingsValues(
  costOfManualAutomation: string,
  costOfAutomatedExecution: string,
  totalSavingsCostAvoided: string,
  totalHoursSavedAvoided: string
) {
  return [
    { label: "Cost of manual automation", value: costOfManualAutomation },
    { label: "Cost of automated execution", value: costOfAutomatedExecution },
    { label: "Total savings/cost avoided", value: totalSavingsCostAvoided },
    { label: "Total hours saved/avoided", value: totalHoursSavedAvoided },
  ];
}
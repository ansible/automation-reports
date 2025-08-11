import { test, expect, Page } from '@playwright/test';
import {
  mockTemplateOptionsRoute,
  mockReportRoute,
  mockReportDetailsRoute,
  mockSettingsRoute,
  mockCostsRoute,
  mockSingleTemplateOptionRoute,
 } from "../support/interceptors.ts";
import { checkCardContent, generateExpectedTotals, generateCostAndSavingsValues } from "../support/helpers.ts";
import reportDetailsWithData from "../fixtures/reportDetailsWithData.json" assert { type: "json"};
import reportDateRange from "../fixtures/reportDateRange.json" assert { type: "json"};
import templateOptions from "../fixtures/templateOptions.json" assert { type: "json"};
import reportResponseByTemplate from "../fixtures/reportResponseByTemplate.json" assert { type: "json"};
import reportDetailsResponseByTemplate from "../fixtures/reportDetailsResponseByTemplate.json" assert { type: "json"};
import reportResponseByOrganization from "../fixtures/reportResponseByOrganization.json" assert { type: "json"};
import reportDetailsResponseByOrganization from "../fixtures/reportDetailsResponseByOrganization.json" assert { type: "json"};
import reportResponseByProject from "../fixtures/reportResponseByProject.json" assert { type: "json"};
import reportDetailsResponseByProject from "../fixtures/reportDetailsResponseByProject.json" assert { type: "json"};
import reportResponseByLabel from "../fixtures/reportResponseByLabel.json" assert { type: "json"};
import reportDetailsReponseByLabel from "../fixtures/reportDetailsReponseByLabel.json" assert { type: "json"};
import reportDateRangePast6Months from "../fixtures/reportDateRangePast6Months.json" assert { type: "json"};
import reportDetailsDateRangePast6Months from "../fixtures/reportDetailsDateRangePast6Months.json" assert { type: "json"};
import reportDetailsResponseAverageCostOfAnEmployee from "../fixtures/reportDetailsResponseAverageCostOfAnEmployee.json" assert { type: "json"};
import reportResponseAverageCostOfAnEmployee from "../fixtures/reportResponseAverageCostOfAnEmployee.json" assert { type: "json"};
import reportDetailsResponseCostPerMinute from "../fixtures/reportDetailsResponseCostPerMinute.json" assert { type: "json"};
import reportResponseCostPerMinute from "../fixtures/reportResponseCostPerMinute.json" assert { type: "json"};
import reportDetailsResponseEnableTemplateCreationTime from "../fixtures/reportDetailsResponseEnableTemplateCreationTime.json" assert { type: "json"};
import reportResponseEnableTemplateCreationTime from "../fixtures/reportResponseEnableTemplateCreationTime.json" assert { type: "json"};
import reportResponseChangeTimeTakenToManuallyExecute from "../fixtures/reportResponseChangeTimeTakenToManuallyExecute.json" assert { type: "json"};
import reportDetailsResponseChangeTimeTakenToManuallyExecute from "../fixtures/reportDetailsResponseChangeTimeTakenToManuallyExecute.json" assert { type: "json"};
import reportResponseUpdateTimeToCreateAutomation from "../fixtures/reportResponseUpdateTimeToCreateAutomation.json" assert { type: "json"};
import reportDetailsResponseUpdateTimeToCreateAutomation from "../fixtures/reportDetailsResponseUpdateTimeToCreateAutomation.json" assert { type: "json"};

async function applyFilter(
  page: Page,
  filterName: string,
  checkboxName: string,
  mockResponse: any,
  mockDetailsResponse: any,
  reportQuery: string,
  detailsQuery: string
) {
  await mockReportRoute(page, mockResponse, reportQuery);
  await mockReportDetailsRoute(page, mockDetailsResponse, detailsQuery);
  await page.getByRole("button", { name: "Template", exact: true }).click();
  await page.getByRole("menuitem", { name: filterName }).click();
  await page.getByRole("button", { name: `Filter by ${filterName}s` }).click();
  await page.getByRole("checkbox", { name: checkboxName, exact: true }).check();
  await expect(page.getByRole("list", { name: filterName }).locator("span").first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Clear all filters" })).toBeVisible();
}

async function verifyCostAndSavingsValues(
  page: Page,
  manualCost: string,
  automatedCost: string,
  savings: string,
  time: string
) {
  const costAndSavingsValues = await generateCostAndSavingsValues(manualCost, automatedCost, savings, time);
  await checkCardContent(page, costAndSavingsValues);
}

test.describe("Set filters", () => {
  test.beforeEach(async ({ page }) => {
    await mockTemplateOptionsRoute(page, templateOptions);
    await mockReportRoute(page, reportDateRange);
    await mockReportDetailsRoute(page, reportDetailsWithData);
    await page.goto("/");
  });

  test("Should filter by templates", async ({ page }) => {
    await applyFilter(
      page,
      "Template",
      "Job template 1",
      reportResponseByTemplate,
      reportDetailsResponseByTemplate,
      "?date_range=month_to_date&job_template=101&page=1&page_size=10&ordering=name",
      "?date_range=month_to_date&job_template=101"
    );
    const expectedTotals = await generateExpectedTotals("32", "0", "10", "4.09");
    await checkCardContent(page, expectedTotals);
  })

  test("Should filter by organization", async ({ page }) => {
    await applyFilter(
      page,
      "Organization",
      "Organization 1",
      reportResponseByOrganization,
      reportDetailsResponseByOrganization,
      "?date_range=month_to_date&organization=11&page=1&page_size=10&ordering=name",
      "?date_range=month_to_date&organization=11"
    );

    const expectedTotals = await generateExpectedTotals("368", "0", "10", "50.53");
    await checkCardContent(page, expectedTotals);
  })

  test("Should filter by project", async ({ page }) => {
    await applyFilter(
      page,
      "Project",
      "Project 10",
      reportResponseByProject,
      reportDetailsResponseByProject,
      "?date_range=month_to_date&project=10&page=1&page_size=10&ordering=name",
      "?date_range=month_to_date&project=10"
    );
    const expectedTotals = await generateExpectedTotals("388", "0", "10", "56.42");
    await checkCardContent(page, expectedTotals);
  })

  test("Should filter by label", async ({ page }) => {
    await applyFilter(
      page,
      "Label",
      "Label 1",
      reportResponseByLabel,
      reportDetailsReponseByLabel,
      "?date_range=month_to_date&label=11&page=1&page_size=10&ordering=name",
      "?date_range=month_to_date&label=11"
    );
    const expectedTotals = await generateExpectedTotals("1,147", "0", "10", "159.40");
    await checkCardContent(page, expectedTotals);
  })

  test("Should clear all filters", async ({ page }) => {
    await mockReportRoute(page, reportDateRange);
    await mockReportDetailsRoute(page, reportDetailsWithData);
    await applyFilter(
      page,
      "Organization",
      "Organization 1",
      reportResponseByOrganization,
      reportDetailsResponseByOrganization,
      "?date_range=month_to_date&organization=11&page=1&page_size=10&ordering=name",
      "?date_range=month_to_date&organization=11"
    );
    await page.getByRole('button', { name: 'Clear all filters' }).click();

    const expectedTotals = await generateExpectedTotals("3,660", "0", "10", "508.76");
    await checkCardContent(page, expectedTotals);
  })

  test("Should change data range to past 6 months", async ({ page }) => {
    await mockReportRoute(
      page,
      reportDateRangePast6Months,
      "?date_range=last_6_month&page=1&page_size=10&ordering=name"
    );
    await mockReportDetailsRoute(page, reportDetailsDateRangePast6Months, "?date_range=last_6_month");
    await page.getByRole('button', { name: 'Month to date' }).click();
    await page.getByRole('menuitem', { name: 'Past 6 months' }).click();

    const expectedTotals = await generateExpectedTotals("50", "0", "10", "8.79");
    await checkCardContent(page, expectedTotals);
  })

  test("Should change curreny to Euro", async ({ page }) => {
    await mockSettingsRoute(page, {"type":"currency","value":2});
    await page.getByRole("button", { name: "British Pound Sterling" }).click();
    await page.getByRole("menuitem", { name: "Euro" }).click();
    await expect(page.getByRole("button", { name: "Euro" })).toBeVisible();
    await expect(page.getByText("€48,321,900.00")).toBeVisible();

    await verifyCostAndSavingsValues(
      page,
      "€48,321,900.00",
      "€2,193,252.16",
      "€46,128,647.84",
      "17,288.19h"
    );
  })

  test("Should change average cost of an employee", async ({ page }) => {
    await mockCostsRoute(page, {"manual_cost_automation":60.0,"automated_process_cost":63.0});
    await mockReportRoute(page, reportResponseAverageCostOfAnEmployee);
    await mockReportDetailsRoute(page, reportDetailsResponseAverageCostOfAnEmployee);
    const input = page.getByRole("spinbutton", { name: "hourly-manual-costs" });
    await input.fill("60");
    await input.press("Enter");

    await verifyCostAndSavingsValues(
      page,
      "£64,429,200.00",
      "£2,283,297.16",
      "£62,145,902.84",
      "17,288.19h",
    );
  })

  test("Should change cost per minute", async ({ page }) => {
    await mockCostsRoute(page, {"manual_cost_automation":45.0,"automated_process_cost":80.0});
    await mockReportRoute(page, reportResponseCostPerMinute);
    await mockReportDetailsRoute(page, reportDetailsResponseCostPerMinute);
    const input = page.getByRole("spinbutton", { name: "hourly-automated-process-costs" });
    await input.fill("80");
    await input.press("Enter");

    await verifyCostAndSavingsValues(
      page,
      "£48,321,900.00",
      "£2,712,188.53",
      "£45,609,711.47",
      "17,288.19h",
    );
  })

  test("Should uncheck time taken to create automation in calculation", async ({ page }) => {
    await mockSettingsRoute(page, {"type":"enable_template_creation_time","value":0});
    await mockReportRoute(page, reportResponseEnableTemplateCreationTime);
    await mockReportDetailsRoute(page, reportDetailsResponseEnableTemplateCreationTime);
    await page.locator("label").filter({ hasText: "Include Time taken to create" }).locator("span").first().click();
    await verifyCostAndSavingsValues(
      page,
      "£48,321,900.00",
      "£1,831,540.15",
      "£46,490,359.85",
      "17,388.24h",
    );
  })

  test("Should update time taken to manually execute", async ({ page }) => {
    const responseBody = {
      "id": 101,
      "name": "Job template 1",
      "description": "description for job_template 1",
      "time_taken_manually_execute_minutes": 160,
      "time_taken_create_automation_minutes": 60
    }
    await mockSingleTemplateOptionRoute(page, 101, responseBody);
    await mockReportRoute(page, reportResponseChangeTimeTakenToManuallyExecute);
    await mockReportDetailsRoute(page, reportDetailsResponseChangeTimeTakenToManuallyExecute);
    const input = page.getByRole('spinbutton', { name: '0-time_taken_manually_execute_minutes' });
    await input.fill("160");
    await input.press("Enter");
    await verifyCostAndSavingsValues(
      page,
      "£49,055,400.00",
      "£2,101,675.15",
      "£46,953,724.85",
      "17,559.86h",
    );
  })

  test("Should update time taken to create automation", async ({ page }) => {
    const responseBody = {
      "id": 101,
      "name": "Job template 1",
      "description": "description for job_template 1",
      "time_taken_manually_execute_minutes": 60,
      "time_taken_create_automation_minutes": 260
    }
    await mockSingleTemplateOptionRoute(page, 101, responseBody);
    await mockReportRoute(page, reportResponseUpdateTimeToCreateAutomation);
    await mockReportDetailsRoute(page, reportDetailsResponseUpdateTimeToCreateAutomation);
    const input = page.getByRole('spinbutton', { name: '0-time_taken_create_automation_minutes' });
    await input.fill("260");
    await input.press("Enter");
    await verifyCostAndSavingsValues(
      page,
      "£48,321,900.00",
      "£2,110,675.15",
      "£46,211,224.85",
      "17,284.86h",
    );
  })

})


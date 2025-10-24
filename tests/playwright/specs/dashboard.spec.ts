import { test, expect } from '@playwright/test';
import {
  mockTemplateOptionsRoute,
  mockReportRoute,
  mockReportDetailsRoute,
 } from "../support/interceptors.ts";
import { loginUser, checkCardContent, generateExpectedTotals, generateCostAndSavingsValues } from "../support/helpers.ts";
import reportDateRangePast6Months from "../fixtures/reportDateRangePast6Months.json" assert { type: "json"};
import reportDetailsDateRangePast6Months from "../fixtures/reportDetailsDateRangePast6Months.json" assert { type: "json"};
import reportDetails from "../fixtures/reportDetails.json" assert { type: "json"};
import templateOptions from "../fixtures/templateOptions.json" assert { type: "json"};
import templates from "../fixtures/templates.json" assert { type: "json"};
import organizations from "../fixtures/organizations.json" assert { type: "json"};
import projects from "../fixtures/projects.json" assert { type: "json"};
import labels from "../fixtures/labels.json" assert { type: "json"};

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await loginUser(
      page,
      templateOptions,
      templates,
      organizations,
      projects,
      labels,
      {"count":0,"next":null,"previous":null,"results":[]},
      reportDetails
    );
    await page.goto("/");
  });

  test("Should show dashboard page", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "Automation Dashboard" })
    ).toBeVisible();
    await expect(
      page.getByText("Discover the significant cost")
    ).toBeVisible();

    const selectReportBtn = page.getByRole("button", { name: "Select a report" });
    await expect(selectReportBtn).toBeVisible();
    await selectReportBtn.click();
    await expect(page.locator("#views-options-menu")).toBeVisible();

    const menuReportItems = page.locator(".pf-v6-c-menu__item-text");
    const count = await menuReportItems.count();
    
    for (let i = 0; i < count; i++) {
      const item = menuReportItems.nth(i);
      await expect(item).toBeVisible();
    }    

    const templateDropdownBtn = page.getByRole("button", { name: "Template", exact: true });
    await expect(templateDropdownBtn).toBeVisible();
    await templateDropdownBtn.click();
    await expect(page.locator("#filter-faceted-options-menu")).toBeVisible();
    const expectedTemplateOptions = ["Label", "Organization", "Project", "Template"];
    const menuTemplateOptions = page.locator("#filter-faceted-options-menu");
    const templateItems = menuTemplateOptions.getByRole("menuitem");
    for (let i = 0; i < expectedTemplateOptions.length; i++) {
      const item = templateItems.nth(i); 
      await expect(item).toContainText(expectedTemplateOptions[i]);
    }

    await expect(page.getByRole("button", { name: "Filter by Templates" })).toBeVisible();

    const dateRangeMonthToDateBtn = page.getByRole("button", { name: "Month to date" });
    await expect(dateRangeMonthToDateBtn).toBeVisible();
    await dateRangeMonthToDateBtn.click();
    await expect(page.locator("#range-dropdown-filter-faceted-date-range")).toBeVisible();
    const dateRangeOptions = [
      "Past year",
      "Past 6 months",
      "Past 3 months",
      "Past month",
      "Year to date",
      "Quarter to date",
      "Month to date",
      "Past 3 years",
      "Past 2 years",
      "Custom",
    ];
    const dateRangeItems = page
      .locator("#range-dropdown-filter-faceted-date-range")
      .getByRole("menuitem");

    for (let i = 0; i < dateRangeOptions.length; i++) {
      const item = dateRangeItems.nth(i);
      await expect(item).toBeVisible();
      await expect(item).toContainText(dateRangeOptions[i]);
    }

    await expect(
      page.getByRole("button", { name: "Save as Report", exact: true })
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "British Pound Sterling" })
    ).toBeVisible();

    const expectedTotals = await generateExpectedTotals("0", "0", "0", "0.00");
    await checkCardContent(page, expectedTotals);

    const expectedChartsData = [
      { label: "Number of times jobs were run", value: "0" },
      { label: "Number of hosts jobs are running on", value: "0" },
    ]
    await checkCardContent(page, expectedChartsData);

    const costAndSavingsValues = [
      { label: "Cost of manual automation", value: "£0.00" },
      { label: "Cost of automated execution", value: "£0.00" },
      { label: "Total savings/cost avoided", value: "£0.00" },
      { label: "Total hours saved/avoided", value: "0.00h" },
    ]
    await checkCardContent(page, costAndSavingsValues);

    const headers = page.locator(".base-table thead.pf-v6-c-table__thead .pf-v6-c-table__tr th");
    const expectedHeaders = [
      "Name",
      "Number of job executions",
      "Host executions",
      "Time taken to manually execute (min)",
      "Time taken to create automation (min)",
      "Running time",
      "Automated cost",
      "Manual cost",
      "Savings",
    ];
    for (let i = 0; i < expectedHeaders.length; i++) {
      await expect(headers.nth(i).locator("div span").nth(0)).toContainText(expectedHeaders[i]);
    }
    await expect(page
      .getByLabel("Sortable table custom toolbar")
      .getByRole("gridcell", { name: "No data available" })
    ).toBeVisible();
  })

  test("Should show dashboard page with data", async ({ page }) => {
    await mockReportRoute(
      page,
      reportDateRangePast6Months,
      "?date_range=last_6_month&page=1&page_size=10&ordering=name"
    );
    await mockReportDetailsRoute(page, reportDetailsDateRangePast6Months, "?date_range=last_6_month");
    await page.getByRole("button", { name: "Month to date" }).click();
    await page.getByRole("menuitem", { name: "Past 6 months" }).click();

    const expectedTotals = await generateExpectedTotals("50", "0", "10", "8.79");
    await checkCardContent(page, expectedTotals);

    const expectedChartsData = [
      { label: "Number of times jobs were run", value: "50" },
      { label: "Number of hosts jobs are running on", value: "239" },
    ]
    await checkCardContent(page, expectedChartsData);
    
    const costAndSavingsValues = await generateCostAndSavingsValues(
      "£644,400.00",
      "£133,268.44",
      "£511,131.56",
      "192.82h"
    );

    await checkCardContent(page, costAndSavingsValues);

    const headers = page.locator(".base-table thead.pf-v6-c-table__thead .pf-v6-c-table__tr th");
    const expectedHeaders = [
      "Name",
      "Number of job executions",
      "Host executions",
      "Time taken to manually execute (min)",
      "Time taken to create automation (min)",
      "Running time",
      "Automated cost",
      "Manual cost",
      "Savings",
    ];
    for (let i = 0; i < expectedHeaders.length; i++) {
      await expect(headers.nth(i).locator("div span").nth(0)).toContainText(expectedHeaders[i]);
    }

    const tdValues = [
      ["Job template 11", "1", "1", "40", "63", "5min 15sec", "£3,165.75", "£1,800.00", "£-1,365.75"],
      ["Job template 13", "1", "5", "60", "60", "13min 21sec", "£3,541.26", "£13,500.00", "£9,958.74"],
      ["Job template 2", "1", "8", "60", "60", "14min 10sec", "£3,592.82", "£21,600.00", "£18,007.18"],
      ["Job template 22", "2", "12", "60", "60", "24min 39sec", "£4,253.74", "£32,400.00", "£28,146.26"],
      ["Job template 23", "2", "11", "60", "60", "14min 18sec", "£3,601.79", "£29,700.00", "£26,098.21"],
      ["Job template 25", "1", "3", "60", "60", "7min 33sec", "£3,176.33", "£8,100.00", "£4,923.67"],
      ["Job template 29", "2", "3", "60", "60", "21min 36sec", "£4,060.80", "£8,100.00", "£4,039.20"],
      ["Job template 3", "2", "12", "60", "60", "20min 19sec", "£3,980.37", "£32,400.00", "£28,419.63"],
      ["Job template 30", "1", "9", "60", "60", "11min 44sec", "£3,439.52", "£24,300.00", "£20,860.48"],
      ["Job template 37", "1", "5", "60", "60", "15min 57sec", "£3,705.53", "£13,500.00", "£9,794.47"],
    ];

    for( let rowI = 0; rowI < tdValues.length; rowI++) {
      const row = tdValues[rowI];
      for (let columnI = 0; columnI < row.length; columnI++) {
        const column = row[columnI];
        const cell = page
          .locator(".base-table tbody .pf-v6-c-table__tr")
          .nth(rowI)
          .locator("td")
          .nth(columnI);

        const input = cell.locator("input");
        const inputCount = await input.count();
    
        if (inputCount > 0) {
          await expect(input).toHaveValue(column);
        } else {
          const span = cell.locator("span");
          await expect(span).toHaveText(column);
        }
      }
    }
  })

  test("Should show an error", async ({ page }) => {
    await mockTemplateOptionsRoute(page, {}, 500);
    await mockReportRoute(
      page,
      {},
      "?date_range=month_to_date&page=1&page_size=10&ordering=name",
      500
    );
    await mockReportDetailsRoute(
      page,
      {},
      "?date_range=month_to_date",
      500
    );
    await expect(
      page.getByRole('heading', { name: 'Something went wrong' })
    ).toBeVisible();
    await expect(
      page.getByText('Please contact your system')
    ).toBeVisible();
  })
})


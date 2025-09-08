import { test, expect, Page } from '@playwright/test';
import {
  mockTemplateOptionsRoute,
  mockFilterSetRoute,
  mockFilterSetReportRoute
 } from "../support/interceptors.ts";
import { loginUser } from "../support/helpers.ts";
import reportDetails from "../fixtures/reportDetails.json" assert { type: "json"};
import templateOptions from "../fixtures/templateOptions.json" assert { type: "json"};
import templateOptionsAddReport from "../fixtures/templateOptionsAddReport.json" assert { type: "json"};

async function saveReport(page: Page, buttonName: string) {
  await page.getByRole("button", { name: buttonName }).click();
}

async function saveAsReportAction(page: Page) {
  await page.getByRole("button", { name: "Save as Report" }).click();
}

async function fillInput(page: Page, value: string) {
  await page.locator("#name").click();
  await page.locator("#name").fill(value);
}

async function selectAReport(page: Page, reportName: string) {
  await page.getByRole("button", { name: "Select a report" }).click();
  await page.getByRole("menuitem", { name: reportName, exact: true }).click();
}

async function selectMenuItem(page: Page, itemName: string, headingName: string) {
  await page.getByRole("menuitem", { name: itemName }).click();
  await expect(page.getByRole("heading", { name: headingName })).toBeVisible();
}

async function deleteReportTest(
  page: Page,
  {
    mockResponse,
    statusCode = 200,
    expectError = false
  }: {
    mockResponse: object;
    statusCode?: number;
    expectError?: boolean;
  }) {
    await mockFilterSetReportRoute(page, 60, mockResponse, statusCode);
    await selectAReport(page, "report_1");
    await saveAsReportAction(page);
    await selectMenuItem(page, "Delete current report", "Delete report");
    await expect(page.getByText("Do you really want to delete the report: report_1")).toBeVisible();
    await saveReport(page, "Delete");
  
    if (expectError) {
      await expect(
        page.getByRole("heading", { name: "Delete report" })
      ).toBeVisible();
    } else {
      await expect(
        page.getByRole("button", { name: "Select a report" })
      ).toBeVisible();
    }
}

async function editReportTest(
  page: Page,
  {
    mockResponse,
    statusCode = 200,
    newReportName,
    expectedFinalSelector,
    expectedFinalText,
    isEdited = false,
  }: {
    mockResponse: object;
    statusCode?: number;
    newReportName: string;
    expectedFinalSelector: Parameters<Page['getByRole']>[0];
    expectedFinalText: string;
    isEdited?: boolean;
  }
) {
    await mockFilterSetReportRoute(page, 60, mockResponse, statusCode);
    await selectAReport(page, "report_1");
    await saveAsReportAction(page);
    await selectMenuItem(page, "Edit current report", "Edit report");
    await expect(page.locator("#name")).toHaveValue("report_1");
    await fillInput(page, newReportName);
    await saveReport(page, "Save");
    if (isEdited) {
      await page.getByRole('button', { name: 'report_1' }).click();
    }
    await expect(
      page.getByRole(expectedFinalSelector, { name: expectedFinalText })
    ).toBeVisible();
}

test.describe("Set report filters", () => {
  test.beforeEach(async ({ page }) => {
    await loginUser(
      page,
      templateOptions,
      {"count":0,"next":null,"previous":null,"results":[]},
      reportDetails
    );
    await page.goto("/");
  });

  test("Should show create a report popup", async ({ page }) => {
    await page.getByRole("button", { name: "Save as Report", exact: true }).click();
    await expect(
      page.locator("#name")
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Create" })
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Cancel" })
    ).toBeVisible();
  })

  test("Should show edit a report popup", async ({ page}) => {
    await selectAReport(page, "report_1");
    await saveAsReportAction(page);
    await selectMenuItem(page, "Edit current report", "Edit report");
    await expect(
      page.locator("#name")
    ).toHaveValue("report_1");
    await expect(
      page.getByRole("button", { name: "Save" })
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Cancel" })
    ).toBeVisible();
  })

  test("Should show delete a report popup", async ({ page}) => {
    await selectAReport(page, "report_1");
    await saveAsReportAction(page);
    await selectMenuItem(page, "Delete current report", "Delete report");
    await expect(
      page.getByText("Do you really want to delete the report: report_1")
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Delete" })
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Cancel" })
    ).toBeVisible();
  })

  test("Should add new report", async ({ page }) => {
    await mockFilterSetRoute(page, {"id":66,"name":"report_3","filters":{"date_range":"month_to_date"}});
    await mockTemplateOptionsRoute(page, templateOptionsAddReport);
    await page.getByRole("button", { name: "Save as Report", exact: true }).click();
    await expect(page.locator("#name")).toBeVisible();
    await fillInput(page, "report_3");
    await saveReport(page, "Create");
    await expect(page.getByRole("button", { name: "report_3" })).toBeVisible();
  })

  test("Should show error when adding report with existing name", async ({ page }) => {
    await mockFilterSetRoute(page, {"name":["Filter name already exists."]}, 400);
    await page.getByRole("button", { name: "Save as Report", exact: true }).click();
    await expect(page.locator("#name")).toBeVisible();
    await fillInput(page, "report_1");
    await saveReport(page, "Create");
    await expect(
      page.getByRole("heading", { 
        name: "Danger alert: Error saving view. Filter name already exists." 
      })
    ).toBeVisible();
  })

  test("Should show internal server error when adding new report", async ({ page }) => {
    await mockFilterSetRoute(page, {}, 500);
    await page.getByRole("button", { name: "Save as Report", exact: true }).click();
    await expect(page.locator("#name")).toBeVisible();
    await fillInput(page, "report_3");
    await saveReport(page, "Create");
    await expect(
      page.getByRole('heading', { name: 'Danger alert: Error saving' })
    ).toBeVisible();
  })

  test("Should edit report", async ({ page }) => {
    await editReportTest(page, {
        mockResponse: {"id":60,"name":"report_10","filters":{"date_range":"month_to_date"}},
        statusCode: 200,
        newReportName: "report_10",
        expectedFinalSelector: "menuitem",
        expectedFinalText: "report_10",
        isEdited: true,
    })
  })

  test("Should show error when editing report with existing name", async ({ page }) => {
    await editReportTest(page, {
        mockResponse: { name: ["Filter name already exists."] },
        statusCode: 400,
        newReportName: "report_2",
        expectedFinalSelector: "heading",
        expectedFinalText: "Danger alert: Error saving view. Filter name already exists.",
      });
  })

  test("Should show internal server error when editing report", async ({ page }) => {
    await editReportTest(page, {
        mockResponse: {},
        statusCode: 500,
        newReportName: "report_2",
        expectedFinalSelector: "heading",
        expectedFinalText: "Danger alert: Error saving view.",
      });
  })

  test("Should delete report", async ({ page }) => {
    await deleteReportTest(page, {
      mockResponse: {},
      statusCode: 200,
      expectError: false
    });
  })

  test("Should show internal server error when delete report", async ({ page }) => {
    await deleteReportTest(page, {
        mockResponse: {},
        statusCode: 500,
        expectError: true
      });
  })
})

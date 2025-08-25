import { test, expect } from '@playwright/test';
import {
  mockAuthSettingsRoute,
  mockTokenRoute,
  mockMeRoute,
  mockTemplateOptionsRoute,
  mockReportRoute,
  mockReportDetailsRoute
} from "../support/interceptors.ts";

import reportDetails from "../fixtures/reportDetails.json" assert { type: "json"};
import templateOptions from "../fixtures/templateOptions.json" assert { type: "json"};

test.describe("Login", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthSettingsRoute(page);
  });

  test("Should show login page", async ({ page }) => {
    await page.goto("/login");
    await expect(
      page.getByRole("heading", { name: "Log in to your account" })
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Login with AAP" })
    ).toBeVisible();
  });
  
  test("Should login user", async ({ page }) => {
    await mockTokenRoute(page);
    await mockMeRoute(page);
    await mockTemplateOptionsRoute(page, templateOptions);
    await mockReportRoute(page, {"count":0,"next":null,"previous":null,"results":[]});
    await mockReportDetailsRoute(page, reportDetails);
    await page.goto("/");
    await expect(
      page.getByRole("button", { name: "Red Hat User" })
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Automation Dashboard" })
    ).toBeVisible();
  });

  test("Should show error message on login failuer", async ({ page }) => {
    await mockAuthSettingsRoute(page, 500);
    await page.goto("/");
    await expect(
      page.getByRole("heading", {
        name: "Danger alert: Something went wrong during authorization. Please contact your system administrator."
      })
    ).toBeVisible();
  })
})


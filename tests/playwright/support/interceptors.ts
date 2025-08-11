export async function mockTemplateOptionsRoute(
  page: import("playwright").Page,
  body: any, 
  status: number = 200
): Promise<void> {
  await page.route("**/api/v1/template_options/", async (route) => {
    await route.fulfill({
      status: status,
      contentType: 'application/json',
      body: JSON.stringify(body),
    });
  });
}

export async function mockSingleTemplateOptionRoute(
  page: import("playwright").Page,
  id: number,
  body: any,
  status: number = 200
): Promise<void> {
  await page.route(`**/api/v1/template_options/${id}`, async (route) => {
    await route.fulfill({
      status: status,
      contentType: 'application/json',
      body: JSON.stringify(body),
    });
  });
}

export async function mockReportRoute(
  page: import("playwright").Page,
  body: any,
  urlParams = "?date_range=month_to_date&page=1&page_size=10&ordering=name",
  status: number = 200,
): Promise<void> {
  await page.route(`**/api/v1/report/${urlParams}`, async (route) => {
    await route.fulfill({
      status: status,
      contentType: 'application/json',
      body: JSON.stringify(body),
    });
  });
}

export async function mockReportDetailsRoute(
    page: import("playwright").Page,
    body: any,
    urlParams = "?date_range=month_to_date",
    status: number = 200,
): Promise<void> {
    await page.route(`**/api/v1/report/details/${urlParams}`, async (route) => {
      await route.fulfill({
        status: status,
        contentType: 'application/json',
        body: JSON.stringify(body),
      });
    });
}

export async function mockFilterSetRoute(
  page: import("playwright").Page,
  body: any,
  status: number = 200,
): Promise<void> {
  await page.route(`**/api/v1/common/filter_set/`, async (route) => {
    await route.fulfill({
      status: status,
      contentType: 'application/json',
      body: JSON.stringify(body),
    });
  });
}

export async function mockFilterSetReportRoute(
  page: import("playwright").Page,
  id: number,
  body: any,
  status: number = 200,
): Promise<void> {
  await page.route(`**/api/v1/common/filter_set/${id}/*`, async (route) => {
    await route.fulfill({
      status: status,
      contentType: 'application/json',
      body: JSON.stringify(body),
    });
  });
}

export async function mockSettingsRoute(
  page: import("playwright").Page,
  body: any,
  status: number = 200,
): Promise<void> {
  await page.route(`**/api/v1/common/settings/`, async (route) => {
    await route.fulfill({
      status: status,
      contentType: 'application/json',
      body: JSON.stringify(body),
    });
  });
}

export async function mockCostsRoute(
  page: import("playwright").Page,
  body: any,
  status: number = 200,
): Promise<void> {
  await page.route(`**/api/v1/costs/`, async (route) => {
    await route.fulfill({
      status: status,
      contentType: 'application/json',
      body: JSON.stringify(body),
    });
  });
}
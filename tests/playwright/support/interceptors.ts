export async function mockAuthSettingsRoute(
  page: import("playwright").Page, 
  status: number = 200
): Promise<void> {
  await page.route("**/api/v1/aap_auth/settings/", async (route) => {
    await route.fulfill({
      status: status,
      contentType: 'application/json',
      body: JSON.stringify({
        "name": "AAP",
        "url": "https://10.44.17.180/o/authorize",
        "client_id": "test_id",
        "scope": "read",
        "approval_prompt": "auto",
        "response_type": "code"
      }),
    });
  });
}

export async function mockTokenRoute(
  page: import("playwright").Page, 
  status: number = 204
): Promise<void> {
  await page.route("**/api/v1/aap_auth/token/", async (route) => {
    await route.fulfill({
      status: status,
      contentType: 'application/json',
      body: JSON.stringify({
        auth_code: "auth_code",
        redirect_uri: "http://localhost:9000/auth-callback"
      }),
    });
  });
}

export async function mockMeRoute(
  page: import("playwright").Page, 
  status: number = 204
): Promise<void> {
  await page.route("**/api/v1/users/me/", async (route) => {
    await route.fulfill({
      status: status,
      contentType: 'application/json',
      body: JSON.stringify({
        "id": 2,
        "first_name": "Red Hat User",
        "last_name": "Red Hat User",
        "email": "user@redhat.si",
        "is_superuser": true,
        "is_platform_auditor": false
    }),
    });
  });
}

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
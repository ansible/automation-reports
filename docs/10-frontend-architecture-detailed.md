# Frontend Architecture — Detailed

## Overview

The frontend is a single-page application (SPA) built with **React 19**, **TypeScript**, and **Vite 8**. It communicates exclusively with the Django backend via a versioned REST API (`/api/v1/`), uses **Zustand** for client-side state, and delegates authentication to AAP's OAuth2 provider.

---

## Component Hierarchy

```mermaid
graph TD
    Root["index.tsx (DOM root)"]
    App["App (index.tsx)"]
    Router["BrowserRouter (react-router-dom v7)"]
    Routes["routes.tsx"]
    Login["Login.tsx\n/login"]
    Callback["AuthCallback\n/auth-callback"]
    Protected["ProtectedRoute\n/"]
    AppLayout["AppLayout.tsx"]
    Header["Header.tsx"]
    Dashboard["Dashboard.tsx"]
    Filters["Filters.tsx"]
    TotalCards["DashboardTotalCards.tsx"]
    Table["DashboardTable.tsx"]
    TopTable["DashboardTopTable.tsx"]
    Bar["DashboardBarChart.tsx"]
    Line["DashboardLineChart.tsx"]
    Views["ViewsSelector.tsx"]
    AddEdit["AddEditView.tsx"]

    Root --> App
    App --> Router
    Router --> Routes
    Routes --> Login
    Routes --> Callback
    Routes --> Protected
    Protected --> AppLayout
    AppLayout --> Header
    AppLayout --> Dashboard
    Dashboard --> Filters
    Dashboard --> Views
    Dashboard --> TotalCards
    Dashboard --> Table
    Dashboard --> TopTable
    Dashboard --> Bar
    Dashboard --> Line
    Table --> AddEdit
```

---

## Routing

```mermaid
flowchart LR
    Browser -->|"/login"| Login
    Browser -->|"/auth-callback?code=..."| Callback
    Browser -->|"/"| Guard{authenticated?}
    Guard -->|"yes"| Dashboard
    Guard -->|"no"| Login
    Login -->|"OAuth redirect"| AAP["AAP /o/authorize/"]
    AAP -->|"?code=..."| Callback
    Callback -->|"POST /api/v1/aap_auth/token/"| BackendToken["Backend JWT issue"]
    BackendToken -->|"GET /api/v1/users/me/"| Dashboard
```

Three routes are registered in `routes.tsx`:

| Path | Component | Guard |
|------|-----------|-------|
| `/login` | `Login` | Redirect to `/` if already authenticated |
| `/auth-callback` | handled inline | None — receives OAuth code |
| `/` | `Dashboard` (inside `AppLayout`) | Redirect to `/login` if not authenticated |

---

## Auth Flow

```mermaid
sequenceDiagram
    participant User
    participant Login as Login.tsx
    participant AAP as AAP OAuth2<br/>/o/authorize/
    participant Backend as Django Backend
    participant authStore as authStore (Zustand)

    User->>Login: visits /login
    Login->>authStore: fetchAppSettings()<br/>GET /api/v1/aap_auth/settings/
    authStore-->>Login: {authorize_url, client_id, redirect_uri}
    User->>Login: click "Log in with AAP"
    Login->>AAP: redirect browser to authorize URL
    AAP->>Login: redirect to /auth-callback?code=ABC
    Login->>authStore: authorizeUser(code, redirect_uri)
    authStore->>Backend: POST /api/v1/aap_auth/token/ {auth_code, redirect_uri}
    Backend-->>authStore: Set-Cookie: access_token (60s), refresh_token (24h)
    authStore->>Backend: GET /api/v1/users/me/
    Backend-->>authStore: {username, is_admin, ...}
    authStore-->>User: redirect to /
```

`Login.tsx` reads the OAuth2 settings (authorize URL, client ID, redirect URI) from the backend via `GET /api/v1/aap_auth/settings/`, then redirects the browser to AAP. On callback, `authorizeUser()` in `authStore` exchanges the code for JWT cookies and hydrates user state.

---

## State Management (Zustand Stores)

```mermaid
graph LR
    subgraph "Store Layer"
        authStore["authStore\n──────────\nuser\nisAuthenticated\nappSettings\n──────────\nfetchAppSettings()\nauthorizeUser()\nrefreshToken()\nlogout()"]
        commonStore["commonStore\n──────────\ncurrency\nfilterSetViews\nenableTemplateCreationTime\n──────────\nfetchCurrency()\nfetchFilterSetViews()\nfetchSettings()"]
        filterStore["filterStore\n──────────\ndateRange\ncostParameters\ntemplateCreationTime\n──────────\nfetchDateRangeOptions()\nfetchCostParameters()\nfetchTemplateOptions()"]
        filterOptionsStore["filterOptionsStore\n──────────\ntemplateOptions[]\nlabelOptions[]\norgOptions[]\nprojectOptions[]\n──────────\n(paginated, debounced)"]
    end

    subgraph "Consumers"
        Dashboard
        Filters
        Header
        DashboardTable
        ViewsSelector
    end

    Dashboard -->|reads| authStore
    Dashboard -->|reads| commonStore
    Dashboard -->|reads| filterStore
    Filters -->|reads/writes| filterOptionsStore
    Filters -->|reads/writes| filterStore
    Header -->|reads| authStore
    ViewsSelector -->|reads| commonStore
    DashboardTable -->|reads| filterStore
```

Each store is a standalone Zustand slice. Components import selectors directly from their respective store files — there is no shared root store.

| Store | File | Manages |
|-------|------|---------|
| `authStore` | `Store/authStore.ts` | Authentication state, JWT refresh, user profile |
| `commonStore` | `Store/commonStore.ts` | Currency, saved filter sets (`FilterSet`), feature flags |
| `filterStore` | `Store/filterStore.ts` | Active date range, cost parameters, creation time toggle |
| `filterOptionsStore` | `Store/filterOptionsStore.ts` | Paginated dropdown options (templates, labels, orgs, projects) |

---

## API Client and Token Refresh

```mermaid
sequenceDiagram
    participant Component
    participant RestService as RestService.ts
    participant apiClient as apiClient.ts (Axios)
    participant Interceptor as requestInterceptors.ts
    participant Backend

    Component->>RestService: getData(params)
    RestService->>apiClient: GET /api/v1/report/?...
    apiClient->>Interceptor: request interceptor fires
    Interceptor->>Interceptor: read csrftoken cookie<br/>set X-XSRF-TOKEN header
    Interceptor->>Backend: request (credentials + XSRF header)
    Backend-->>Interceptor: 401 Unauthorized (access_token expired)
    Interceptor->>Backend: POST /api/v1/aap_auth/refresh_token/
    Backend-->>Interceptor: new access_token cookie set
    Interceptor->>Backend: retry original request
    Backend-->>apiClient: 200 OK {data}
    apiClient-->>RestService: response
    RestService-->>Component: typed data
```

`apiClient.ts` creates a single Axios instance:
- `baseURL` from `VITE_API_URL` env var
- `withCredentials: true` — sends `HttpOnly` JWT cookies automatically
- XSRF token auto-injected from `csrftoken` cookie into `X-XSRF-TOKEN` header

`requestInterceptors.ts` handles **silent token refresh**: on a 401 it POSTs to `/api/v1/aap_auth/refresh_token/`, the backend issues a new access cookie, and the original request is retried transparently.

All API call definitions live in one file — `Services/RestService.ts`. No component makes a direct Axios call.

---

## Dashboard Data Flow

```mermaid
flowchart TD
    Mount["Dashboard mounts"]
    FetchInit["Bootstrap fetch\n- fetchDateRangeOptions()\n- fetchCostParameters()\n- fetchCurrency()\n- fetchFilterSetViews()\n- fetchSettings()"]
    FetchReport["Report fetch\n- GET /api/v1/report/ (paginated list)\n- GET /api/v1/report/details/ (aggregates + chart data)\n- GET /api/v1/template_options/"]
    Interval["setInterval\nDATA_REFRESH_INTERVAL_SECONDS (60s)"]
    FilterChange["User changes filter\n(org / template / project / label / date)"]
    UpdateStore["filterStore updated"]
    Refetch["Refetch with new params"]
    Render["Render components:\n- DashboardTotalCards (KPI tiles)\n- DashboardTable (job template list)\n- DashboardBarChart\n- DashboardLineChart\n- DashboardTopTable"]

    Mount --> FetchInit
    FetchInit --> FetchReport
    FetchReport --> Render
    Render --> Interval
    Interval --> FetchReport
    Render --> FilterChange
    FilterChange --> UpdateStore
    UpdateStore --> Refetch
    Refetch --> Render
```

---

## Chart Layer

```mermaid
graph LR
    subgraph "Chart Components"
        BarChart["DashboardBarChart\n(bar chart)"]
        LineChart["DashboardLineChart\n(line/area chart)"]
        TotalCards["DashboardTotalCards\n(KPI stat tiles)"]
        TopTable["DashboardTopTable\n(top users/projects)"]
        Table["DashboardTable\n(paginated job templates)"]
    end

    subgraph "Libraries"
        PFCharts["@patternfly/react-charts\n(wraps victory-*)"]
        VictoryRaw["victory-* packages\n(direct, also installed)"]
        PFCore["@patternfly/react-core\n(layout, cards, table)"]
    end

    BarChart --> PFCharts
    LineChart --> PFCharts
    PFCharts -.->|"internally depends on"| VictoryRaw
    TotalCards --> PFCore
    TopTable --> PFCore
    Table --> PFCore
```

`@patternfly/react-charts` already bundles `victory` as a peer dependency. The raw `victory-*` packages in `package.json` are redundant — they add CVE surface with no benefit. See the Recommendations doc.

---

## Filter System

```mermaid
flowchart LR
    Filters["Filters.tsx"]
    DateRange["DateRangePicker.tsx\n(preset or custom range)"]
    OrgDD["BaseDropdown\n(organizations, paginated)"]
    TplDD["MultiChoiceDropdown\n(templates, paginated)"]
    ProjDD["BaseDropdown\n(projects, paginated)"]
    LabelDD["BaseDropdown\n(labels, paginated)"]
    Currency["CurrencySelector.tsx"]
    ViewsSel["ViewsSelector.tsx\n(saved filter sets)"]

    Filters --> DateRange
    Filters --> OrgDD
    Filters --> TplDD
    Filters --> ProjDD
    Filters --> LabelDD
    Filters --> Currency
    Filters --> ViewsSel

    OrgDD --> filterOptionsStore
    TplDD --> filterOptionsStore
    ProjDD --> filterOptionsStore
    LabelDD --> filterOptionsStore
    DateRange --> filterStore
    Currency --> commonStore
    ViewsSel --> commonStore
```

Filter options are fetched lazily and paginatedly from `/api/v1/organizations/`, `/api/v1/labels/`, `/api/v1/projects/`, and `/api/v1/template_options/`. Changes are written into Zustand stores which trigger a dashboard re-fetch.

---

## Build Pipeline

```mermaid
flowchart LR
    TS["TypeScript 6\n(strict)"] --> SWC["@vitejs/plugin-react-swc\n(Rust SWC transpiler)"]
    SWC --> Vite["Vite 8 bundler"]
    SCSS["sass\n(PatternFly SCSS)"] --> Vite
    Vite --> Dist["src/frontend/dist/\nindex.html + assets/"]
    Dist --> Nginx["nginx (production)\nserves SPA at /\nproxies /api/ → uwsgi"]
    Vite -->|"dev :5173"| DevProxy["proxy /api/ → :9000\n(Django dev server)"]
```

- Alias `@app` → `src/frontend/app/` (configured in both `vite.config.ts` and `tsconfig.json`)
- `rollup-plugin-visualizer` available for bundle size analysis

---

## E2E Test Structure

```mermaid
graph TD
    Config["playwright.config.ts\nbaseURL: http://localhost:5173"]
    Config --> Specs
    subgraph "Specs (tests/playwright/specs/)"
        Dashboard["dashboard.spec.ts"]
        Login["login.spec.ts"]
        SetFilters["setFilters.spec.ts"]
        ReportFilters["setReportFilters.spec.ts"]
        Inputs["testInputs.spec.ts"]
    end
    Helpers["support/helpers.ts"] --> Specs
    Interceptors["support/interceptors.ts\n(request interception)"] --> Specs
    Fixtures["fixtures/*.json\n30+ pre-recorded API responses"] --> Interceptors
```

Tests run against a live dev server with API calls intercepted via pre-recorded JSON fixtures — no real AAP cluster required.

---

## Key File Reference

| File | Path | Role |
|------|------|------|
| DOM entry | `src/frontend/index.tsx` | Root mount |
| App shell | `src/frontend/app/index.tsx` | Router wrapper |
| Routes | `src/frontend/app/routes.tsx` | Route definitions + auth guards |
| Auth store | `src/frontend/app/Store/authStore.ts` | OAuth2 flow, JWT state |
| Common store | `src/frontend/app/Store/commonStore.ts` | Currency, filter sets, settings |
| Filter store | `src/frontend/app/Store/filterStore.ts` | Active filters |
| Filter options | `src/frontend/app/Store/filterOptionsStore.ts` | Paginated dropdown options |
| API client | `src/frontend/app/client/apiClient.ts` | Axios instance |
| Interceptors | `src/frontend/app/client/requestInterceptors.ts` | Token refresh, XSRF |
| All API calls | `src/frontend/app/Services/RestService.ts` | Single HTTP call source |
| Dashboard | `src/frontend/app/Dashboard/Dashboard.tsx` | Main view, polling, filter wiring |
| Layout | `src/frontend/app/AppLayout/AppLayout.tsx` | Navigation shell |
| Types | `src/frontend/app/Types/` | All TypeScript interfaces |

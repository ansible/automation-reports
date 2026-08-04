# Recommendations — Dependency Reduction and Architecture Improvements

## Priority Matrix

| Item | Impact | Effort | CVE Reduction | Priority |
|------|--------|--------|---------------|----------|
| Remove raw `victory-*` JS packages | Medium | Low | Medium | **High** |
| Remove `django-channels` + `channels_redis` | High | Medium | High | **High** |
| Replace `uwsgi` with `gunicorn` | High | Low | High | **High** |
| Remove `ansible-runner` | High | Medium | High | **High** |
| Replace `pytz` with stdlib `zoneinfo` | Low | Low | Low | Medium |
| Remove `django-solo` (DIY singleton) | Low | Low | Low | Medium |
| Remove `split-settings` | Low | Low | Low | Medium |
| Remove `sirv-cli` (frontend) | Low | Trivial | Low | Medium |
| Replace `requests` with `httpx` | Low | Medium | Low | Low |
| Replace `WeasyPrint`/`django-weasyprint` | Medium | High | High | Low |
| Replace polling with SSE | Medium | High | None | Low |

---

## 1. JavaScript: Remove Redundant `victory-*` Packages

### Problem

`package.json` currently lists both `@patternfly/react-charts` **and** the raw `victory-*` family as direct dependencies:

```json
"@patternfly/react-charts": "8.4.1",
"victory-bar": "37.3.6",
"victory-line": "37.3.6",
"victory-area": "37.3.6",
"victory-chart": "37.3.6",
...
```

`@patternfly/react-charts` already re-exports Victory components and manages the `victory` peer dependency internally. Installing `victory-*` separately means:
- Duplicate copies of Victory can end up in the bundle if versions drift
- Every `victory-*` package is an additional CVE surface and audit entry
- `npm audit` noise grows proportionally
- Bundle size increases

The chart components in `src/frontend/app/Dashboard/` (`DashboardBarChart.tsx`, `DashboardLineChart.tsx`) should import from `@patternfly/react-charts` only.

### Action

1. Audit imports across `src/frontend/app/Dashboard/` and `src/frontend/app/Components/` for any `import ... from 'victory-*'`
2. Replace all direct `victory-*` imports with `@patternfly/react-charts` equivalents
3. Remove all `victory-*` entries from `package.json`
4. Run `npm install` and `npm run build` to verify

```bash
# Find direct victory imports
grep -r "from 'victory" src/frontend/app/
```

---

## 2. Python: Remove `django-channels` and `channels_redis`

### Problem

The application has two ASGI-capable frameworks installed:

| Package | Version | Purpose stated |
|---------|---------|---------------|
| `channels` | 4.3.2 | Django Channels (WebSocket / ASGI layer) |
| `channels_redis` | 4.3.0 | Redis channel layer backend for Channels |

However:
- The application uses **HTTP polling** only — no WebSocket endpoints exist in any `urls.py`
- Background tasks use **dispatcherd + pg_notify**, not Channels consumers
- The `asgi.py` file exists but production serving goes through **uWSGI (WSGI)**, not an ASGI server
- `uvicorn` is listed as a dependency but is not the production entrypoint (supervisord starts uwsgi)

Django Channels is a large dependency (`daphne`, `autobahn`, `twisted` or `aiohttp` transports) and its Redis backend (`channels_redis`) adds an additional attack surface on top of the Redis client already present. If WebSockets are not used, both packages can be removed entirely.

### Action

1. Confirm no WebSocket consumers exist:
   ```bash
   grep -r "WebsocketConsumer\|AsyncWebsocketConsumer\|channels.routing" src/backend/
   ```
2. Check `asgi.py` — if it just wraps the Django WSGI app with `channels`, simplify it to Django's native ASGI support:
   ```python
   # src/backend/django_config/asgi.py (simplified)
   import os
   from django.core.asgi import get_asgi_application
   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_config.settings')
   application = get_asgi_application()
   ```
3. Remove from `settings.py`: `CHANNEL_LAYERS`, `ASGI_APPLICATION` (if set to a Channels routing config)
4. Remove from `requirements-pinned.txt`: `channels`, `channels_redis`
5. Remove from `INSTALLED_APPS`: `'channels'`
6. Run the full test suite to confirm nothing breaks

**CVE impact:** Channels and Channels-Redis have had multiple security advisories. Removing them eliminates this entire attack surface.

---

## 3. Python: Replace `uwsgi` with `gunicorn`

### Problem

`uwsgi` (version 2.0.31) is a C extension written in C that has accumulated a long CVE history. It is large, complex, and requires a C compiler to build (adding toolchain risk in the build stage). Key concerns:

- Several memory-safety CVEs in the uwsgi C core in recent years
- Requires compilation from source in the Python builder stage
- Configuration (`uwsgi.ini`, `supervisord` configs) adds operational complexity

`gunicorn` is a pure-Python WSGI server with a much smaller attack surface, no C compilation required, and is the standard choice for Django in containerized deployments.

### Action

1. Remove `uwsgi` from `requirements-pinned.txt`
2. Add `gunicorn>=23.0.0`
3. Update `docker/supervisord_dashboard_web.conf`:
   ```ini
   [program:dashboard_web]
   command=/venv/bin/gunicorn django_config.wsgi:application
       --workers 4
       --worker-class sync
       --bind unix:/run/dashboard.sock
       --timeout 120
       --access-logfile -
       --error-logfile -
   ```
4. Update `docker/nginx.conf` to proxy to the Unix socket instead of the uwsgi protocol
5. Update the Dockerfile builder stage — remove the Rust/C toolchain that was needed for uwsgi compilation

---

## 4. Python: Remove `ansible-runner`

### Problem

`ansible-runner` is a large library (~20 transitive dependencies including `pexpect`, `packaging`, `docutils`, and more) originally designed to run Ansible playbooks programmatically. It is listed as a runtime dependency but the codebase does not appear to invoke it in any application path — all background work goes through dispatcherd tasks that call the AAP REST API directly.

**To verify:**
```bash
grep -r "ansible_runner\|import ansible_runner\|from ansible_runner" src/backend/
```

If no results: remove it unconditionally.

If it is used (e.g. in a management command), evaluate whether the same operation can be done via the AAP REST API or a `subprocess` call, eliminating the large transitive dep tree.

### Action

1. Run the grep above
2. If unused: remove from `requirements-pinned.txt`
3. Run the full test suite

---

## 5. Python: Replace `pytz` with stdlib `zoneinfo`

### Problem

`pytz` is a pre-Python 3.9 workaround for timezone handling. Since Python 3.9, the standard library includes `zoneinfo` (PEP 615), which is fully compatible with Django when `USE_TZ = True`. Keeping `pytz` adds a third-party dependency for functionality the language now provides natively.

Django itself migrated away from requiring pytz in Django 4.0.

### Action

Search for usages:
```bash
grep -r "import pytz\|from pytz" src/backend/
```

For each usage, replace:
```python
# Before
import pytz
tz = pytz.timezone('America/New_York')
dt = datetime.datetime.now(tz)

# After
from zoneinfo import ZoneInfo
tz = ZoneInfo('America/New_York')
dt = datetime.datetime.now(tz)
```

Remove `pytz` from `requirements-pinned.txt`.

---

## 6. Python: Remove `django-solo`

### Problem

`django-solo` provides singleton model support (used by `SubscriptionCost` and `SyncScheduleState`). The package is small but introduces a dependency for a pattern that is trivially implemented inline.

### Replacement

```python
class SingletonModel(models.Model):
    class Meta:
        abstract = True

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
```

Apply this base class to `SubscriptionCost` and `SyncScheduleState`, then remove `django-solo` from requirements and `INSTALLED_APPS`.

---

## 7. Python: Remove `split-settings`

### Problem

`split-settings` (version 1.0.0) is used to load `*.py` files from `DASHBOARD_SETTINGS_DIR`. This is a convenience wrapper around a pattern achievable with three lines of Python:

```python
import glob, importlib.util, os

for path in sorted(glob.glob(os.path.join(os.environ.get('DASHBOARD_SETTINGS_DIR', ''), '*.py'))):
    spec = importlib.util.spec_from_file_location('_override', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for k, v in vars(mod).items():
        if not k.startswith('_'):
            globals()[k] = v
```

Remove from `requirements-pinned.txt` and `INSTALLED_APPS` and inline this logic in `settings.py`.

---

## 8. Frontend: Remove `sirv-cli`

### Problem

`sirv-cli` is a static file server used in development or lightweight production serving. In production, nginx serves the SPA. In development, Vite's built-in dev server (`vite dev`) is used. `sirv-cli` is neither the production path nor the development path and appears unused.

```bash
grep -r "sirv" package.json Makefile docker/
```

If it only appears in `package.json` and not in any `Makefile` target or Docker entrypoint, remove it:

```bash
npm uninstall sirv-cli
```

---

## 9. Python: Replace `requests` with `httpx` (Optional, Low Priority)

### Problem

`requests` (version 2.32.5) is used in `apps/clusters/connector.py` for synchronous HTTP calls to the AAP REST API. While `requests` is widely used and maintained, `httpx` provides a drop-in-compatible API with:
- Built-in async support (useful if the connector is ever moved to async tasks)
- Better timeout handling
- HTTP/2 support
- Actively maintained with a smaller CVE history

This is low priority as `requests` is well-maintained, but worth tracking for the next major dependency refresh.

---

## 10. Python: Evaluate `WeasyPrint` / `django-weasyprint` (PDF Generation)

### Problem

PDF generation via WeasyPrint (`django-weasyprint` 2.4.0 → `weasyprint`) pulls in a large C dependency chain:
- `Pango` (text layout)
- `Cairo` (2D graphics)
- `cffi` (C foreign function interface)
- `fonttools`
- `cssselect2`, `html5lib`, `tinycss2`

These C libraries have a history of memory-safety CVEs and significantly increase the container image size and build complexity. They must be present in the final runtime image.

### Alternatives

| Option | Tradeoffs |
|--------|-----------|
| **ReportLab** | Pure Python, smaller, but requires more custom layout code |
| **Puppeteer/Playwright (headless Chrome)** | Renders actual HTML/CSS perfectly; adds a browser binary (large); better for complex layouts |
| **Move PDF to frontend** | `jsPDF` or `react-pdf` — generate PDF in browser, remove server dependency entirely |
| **Keep WeasyPrint** | Simplest path if PDF quality is acceptable and CVEs are managed via base image updates |

The most impactful reduction: move PDF generation to the frontend using a JS library. The report data is already available client-side; generating the PDF there eliminates all WeasyPrint C library dependencies from the server.

---

## 11. Architecture: Replace Dashboard Polling with Server-Sent Events

### Problem

`Dashboard.tsx` polls all report endpoints every `DATA_REFRESH_INTERVAL_SECONDS` (default 60 seconds) using `setInterval`. This means:
- N active browser sessions = N×(number of endpoints) requests per minute hitting the backend
- Data can be stale for up to 60 seconds
- No mechanism to push urgent updates

### Recommendation

Replace polling with **Server-Sent Events (SSE)**. SSE is a standard HTTP mechanism for server-to-client push with automatic reconnection, requiring no WebSocket infrastructure.

```python
# Backend: apps/clusters/views.py
from django.http import StreamingHttpResponse
import json, time

def report_sse(request):
    def event_stream():
        while True:
            data = serialize_current_report(request)
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(30)
    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')
```

```typescript
// Frontend: Dashboard.tsx
const source = new EventSource('/api/v1/report/stream/', { withCredentials: true });
source.onmessage = (e) => {
  const data = JSON.parse(e.data);
  updateDashboard(data);
};
```

This removes the polling `setInterval` entirely, reduces load under heavy concurrency, and delivers fresher data. SSE works over standard HTTP — no Channels required.

---

## 12. Architecture: Decouple `ClusterSyncData.save()` Side Effect

### Problem

`ClusterSyncData.save()` automatically creates a `SyncJob(PARSE_JOB_DATA)` as a side effect. This tight coupling:
- Makes the model's `save()` do two things (persist + queue work)
- Is invisible from the model interface — violates the principle of least surprise
- Makes unit testing harder (saving a `ClusterSyncData` fixture triggers a real `SyncJob`)

### Recommendation

Move the `SyncJob` creation out of `save()` and into the task that creates `ClusterSyncData`:

```python
# In AAPSyncTask (apps/tasks/jobs.py):
sync_data = ClusterSyncData.objects.create(cluster=cluster, raw_data=data)
SyncJob.objects.create(
    cluster=cluster,
    job_type=SyncJob.PARSE_JOB_DATA,
    status=SyncJob.PENDING,
)
pg_notify('automation_dashboard_parse_channel', sync_data.pk)
```

This makes the relationship explicit, testable, and easy to trace.

---

## 13. Security: Harden JWT Token Storage

### Current State

- `access_token`: `HttpOnly`, `SameSite=Lax`, 60-second lifetime
- `refresh_token`: `HttpOnly`, `SameSite=Lax`, 24-hour lifetime

### Recommendations

| Setting | Current | Recommended |
|---------|---------|-------------|
| Cookie `Secure` flag | Unknown | Always set `Secure=True` in production (HTTPS-only) |
| `SameSite` | `Lax` | Consider `Strict` if the app is never embedded in cross-site iframes |
| Refresh token rotation | Yes (per-use) | Confirm — each refresh should invalidate the old token |
| `__Host-` prefix | Not used | Use `__Host-access_token` to prevent subdomain fixation attacks |

Ensure `SESSION_COOKIE_SECURE = True` and `CSRF_COOKIE_SECURE = True` are set in production settings.

---

## 14. Dependency Audit Automation

Add automated CVE scanning to the CI pipeline:

```yaml
# .github/workflows/security.yml (additions)
- name: Python vulnerability scan
  run: pip-audit -r requirements-pinned.txt --format json -o pip-audit.json

- name: JavaScript vulnerability scan
  run: npm audit --audit-level=moderate --json > npm-audit.json

- name: Upload audit reports
  uses: actions/upload-artifact@v4
  with:
    name: security-audit
    path: "*-audit.json"
```

Block merges when `pip-audit` or `npm audit` reports CRITICAL severity findings.

---

## Summary: Dependencies to Remove

### Python (`requirements-pinned.txt`)

| Package | Reason to Remove | Replacement |
|---------|-----------------|-------------|
| `channels` | No WebSockets used | None (or SSE) |
| `channels_redis` | No WebSockets used | None |
| `ansible-runner` | Likely unused | None |
| `pytz` | Superseded by stdlib | `zoneinfo` |
| `django-solo` | Trivially replaceable | Inline singleton |
| `split-settings` | Trivially replaceable | Inline glob loader |
| `uwsgi` | CVE surface, C build | `gunicorn` |
| `django-weasyprint` + WeasyPrint | Heavy C dep chain | Frontend PDF or ReportLab |

### JavaScript (`package.json`)

| Package | Reason to Remove | Replacement |
|---------|-----------------|-------------|
| `victory-bar` | Duplicate — PF charts wraps Victory | `@patternfly/react-charts` |
| `victory-line` | Duplicate | `@patternfly/react-charts` |
| `victory-area` | Duplicate | `@patternfly/react-charts` |
| `victory-chart` | Duplicate | `@patternfly/react-charts` |
| `victory-*` (all) | Duplicate | `@patternfly/react-charts` |
| `sirv-cli` | Unused in prod and dev | None |

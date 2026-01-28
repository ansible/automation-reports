# Translations Quick Start

This project supports internationalization (i18n) for both frontend and backend.

## Frontend (i18next)

The frontend uses [i18next](https://www.i18next.com/) with React bindings.

### Key Files

- `src/frontend/app/i18n/config.ts` - i18next configuration
- `src/frontend/locales/{lang}/translation.json` - translation files
- `i18next-parser.config.cjs` - extraction configuration

### Using Translations in Code

```tsx
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  return <h1>{t('My translatable text')}</h1>;
}
```

Key pattern: **English text is the key**. No separate key identifiers — the English string itself is used as the lookup key.

### Adding New Strings

1. Use the `t()` function with English text in your component
2. Run extraction:
   ```bash
   npm run i18n
   ```
3. Translation files in `src/frontend/locales/*/translation.json` are updated automatically
4. Provide translations for non-English locales

---

## Backend (Django gettext)

The backend uses Django's standard gettext-based translation system.

### Key Files

- `src/backend/locale/{lang}/LC_MESSAGES/django.po` - message catalogs
- `src/backend/locale/{lang}/LC_MESSAGES/django.mo` - compiled message files
- `src/backend/django_config/settings.py` - i18n settings (`LANGUAGES`, `LOCALE_PATHS`)

### Using Translations in Code

```python
from django.utils.translation import gettext_lazy as _

class MyModel(models.Model):
    name = models.CharField(verbose_name=_('Name'))

# For runtime translation (views, serializers):
from django.utils.translation import gettext as _
error_msg = _('Something went wrong')
```

Use `gettext_lazy` (aliased as `_`) for model fields and class-level strings. Use `gettext` for runtime strings.

### Extracting and Compiling Messages

With Docker Compose running:

```bash
# Extract strings from Python code
make makemessages

# Compile .po files to .mo
make compilemessages

# Or both together
make translations
```

Without Docker (from `src/backend`):
```bash
python manage.py makemessages -l en -l es -l fr -l de -l zh -l ja --ignore=venv
python manage.py compilemessages
```

### Workflow for New Backend Strings

1. Mark strings with `_()` in your Python code
2. Run `make makemessages`
3. Edit the `.po` files in `src/backend/locale/*/LC_MESSAGES/` to add translations
4. Run `make compilemessages`
5. Restart the backend service

---

## Translation Workflow Summary

| Task | Frontend | Backend |
|------|----------|---------|
| Mark string | `t('text')` | `_('text')` |
| Extract | `npm run i18n` | `make makemessages` |
| Files | `locales/{lang}/translation.json` | `locale/{lang}/LC_MESSAGES/django.po` |
| Compile | N/A (JSON used directly) | `make compilemessages` |

---

## Language Detection

- **Frontend**: Browser language, localStorage (`automation-dashboard-i18n`), or `?lang=` query param
- **Backend**: `Accept-Language` header via Django's `LocaleMiddleware`

## Adding a New Language

1. **settings.py**: Add to `LANGUAGES` list
2. **Frontend**: Add language code to `locales` array in `i18next-parser.config.cjs` and `src/frontend/app/i18n/languages.ts`
3. Run extraction commands for both frontend and backend
4. Create/update translation files

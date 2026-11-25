# CV Maker Pro

Full CV-building platform implementing PRD v2.0: **Flutter Android app + Python Django + MySQL + Tailwind CSS**.

- `backend/` - Django project: DRF APIs (`/api/v1/`), Tailwind admin panel (`/panel/`), PDF processing (PyMuPDF, pdfplumber, Pillow, reportlab), 14 apps (`accounts`, `resumes`, `templates_manager`, `template_importer`, `ai_tools`, `ai_providers`, `ats_checker`, `advertisements`, `rewards`, `exports`, `shared_assets`, `notifications`, `admin_dashboard`, `system_settings`)
- `mobile/` - Flutter Android app (see `mobile/README.md`)
- `docs/` - the governing PRD (`PRD.md`) plus API, database and deployment docs

## Documentation

- [docs/PRD.md](docs/PRD.md) - Product Requirements v2.0 (Django stack)
- [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) - all `/api/v1/` endpoints + Template JSON schema v1.0
- [docs/DATABASE.md](docs/DATABASE.md) - data model and integrity rules
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - backend + Flutter setup, AdMob SSV config, security checklist

## Backend quick start

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill real values (MySQL, SECRET_KEY, FIELD_ENCRYPTION_KEY)
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

SQLite fallback for tests/dev: `DJANGO_DB_ENGINE=sqlite DJANGO_DEBUG=True`

```bash
DJANGO_DB_ENGINE=sqlite DJANGO_DEBUG=True python3 manage.py test apps
```

## Key behaviours

- Template JSON schema v1.0 (`apps/templates_manager/schema.py`) is the single
  source of truth shared by the importer, admin builder, Flutter renderer and
  server PDF renderer
- AdMob rewarded ads verified via SSV (Ed25519) with unique transaction IDs;
  credits granted only after the required ad count; AI credits and export
  unlocks are independent with atomic reserve/consume/release lifecycle
- AI provider routing with failover, retries, circuit breaker, budgets and
  encrypted-at-rest API keys
- ATS checker is rule-based with an explicit "estimated indicator" disclaimer

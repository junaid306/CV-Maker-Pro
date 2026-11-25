# CV Maker Pro - Deployment Guide

Stack: Django (APIs + admin panel + PDF processing) + MySQL + Flutter Android app.

## 1. Backend

### Requirements
Python 3.10+ (tested on 3.12). Create a virtualenv and install:

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment
Copy `.env.example` to `.env` and fill real values (never commit `.env`):

```env
DJANGO_SECRET_KEY=<long-random-secret>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,10.0.0.5
FIELD_ENCRYPTION_KEY=<base64 urlsafe key, e.g. from python: base64.urlsafe_b64encode(os.urandom(32))>

DB_ENGINE=mysql
DB_NAME=cv_maker
DB_USER=cv_maker_user
DB_PASSWORD=<password>
DB_HOST=127.0.0.1
DB_PORT=3306

MAX_PDF_UPLOAD_MB=10
MAX_PDF_PAGES=10
```

`FIELD_ENCRYPTION_KEY` encrypts AI provider API keys (Fernet). In DEBUG mode a
fallback key is derived from SECRET_KEY so local dev works without setup.

### Database
Create the MySQL database and user, then:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

### Run
Development: `python manage.py runserver`
Production: gunicorn + nginx (or any WSGI host):

```bash
gunicorn config.wsgi:application --workers 3 --bind 127.0.0.1:8000
```

### Admin panel
- Custom panel (Tailwind): `/panel/`
- Django built-in admin: `/admin/`

### AI providers
In the admin panel (`panel/providers/`) add providers like Groq, OpenRouter,
OpenAI, Gemini, Anthropic; paste API keys (stored encrypted), set priority and
budgets. Use "Test connection" to verify.

### AdMob SSV
Configure in `panel/ads/`:
- Enable rewarded ads, set `required_ads` per purpose (default 5).
- Set the AdMob SSV callback URL to `https://<your-domain>/api/v1/ads/ssv/`.
- Paste the SSV public key PEM override (or leave empty to fetch Google keys).

### Optional background jobs
Celery/Redis are commented out in `requirements.txt`. Import jobs and AI
generation currently run synchronously; switch to Celery for high volume
(`settings` and service entry points are structured for it).

## 2. Flutter app

```bash
cd mobile
flutter create . --org com.cvmakerpro --project-name cv_maker_pro
flutter pub get
flutter run --dart-define=API_BASE_URL=https://<your-domain>/api/v1
```

Build the release APK:

```bash
flutter build apk --release \
  --dart-define=API_BASE_URL=https://<your-domain>/api/v1 \
  --dart-define=ADMOB_APP_ID=ca-app-pub-XXXX~YYYY \
  --dart-define=ADMOB_REWARDED_UNIT_ID=ca-app-pub-XXXX/YYYY
```

The Android emulator reaches a PC-hosted backend via `http://10.0.2.2:8000/api/v1`.

## 3. Security checklist

- `DJANGO_DEBUG=False` in production; `FIELD_ENCRYPTION_KEY` set
- MySQL user limited to the `cv_maker` database only
- HTTPS everywhere (SSV callbacks must be TLS)
- `.env` never committed; secrets rotate with `FIELD_ENCRYPTION_KEY`
- Throttling enabled on auth/AI/upload scopes

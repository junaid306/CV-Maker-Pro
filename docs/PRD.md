# CV Maker — Complete PRD & App Flow
## Updated Technology Stack: Flutter + Python Django + MySQL + Tailwind CSS

**Document version:** 2.0  
**Updated:** 25 November 2026  
**Project type:** Android CV Maker with a web-based Admin Panel  
**Monetization:** Advertisements only — no paid plans or subscriptions

---

## 1. Project Overview

Build a Canva-like CV Maker platform with:

1. A Flutter Android application for users.
2. A single Python Django backend.
3. Django REST Framework APIs for the Flutter app.
4. A Django-powered web Admin Panel using Django Templates and Tailwind CSS.
5. MySQL as the main database.
6. Python-based PDF processing and PDF-to-JSON template conversion inside the same Django project.

**Important architecture decision:** There is no Laravel, Node.js, Express.js, React Admin Panel, or separate Python PDF microservice in this version. The backend, REST APIs, admin web interface, and PDF processing are handled by one Django project. Flutter remains a separate mobile application.

Tailwind CSS is a frontend styling framework, not a backend. It will style the Django-rendered Admin Panel.

---

## 2. Final Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| User mobile app | Flutter + Dart | Android application |
| Backend | Python + Django | Main application backend |
| Mobile API | Django REST Framework | REST APIs for Flutter |
| Admin Panel | Django Templates + Tailwind CSS | Web-based administration |
| Database | MySQL | Persistent application data |
| ORM | Django ORM | Database models and queries |
| Authentication | Django authentication + DRF token/JWT approach | User and admin authentication |
| PDF processing | PyMuPDF, pdfplumber, Pillow | PDF parsing and preview generation |
| OCR | Tesseract OCR (optional) | Scanned PDF text extraction |
| Background jobs | Celery + Redis (optional, recommended for production) | Long-running PDF and AI tasks |
| File storage | Local media during development; S3-compatible storage in production | PDFs, images and assets |
| AI providers | Provider adapters in Django | AI generation and ATS analysis |
| Ads | Google AdMob in Flutter + server-side verification endpoint | Ad monetization and reward verification |

Use a currently supported Python and Django release compatible with the selected dependencies. Pin tested dependency versions in `requirements.txt`.

---

## 3. Product Rules and Monetization

The app is free to use and earns revenue only through advertisements.

- No paid plans.
- No subscriptions.
- No premium templates.
- No template purchases.
- No payment gateway.
- No watermark.
- All templates and editor features are free.
- Rewarded ads may unlock AI generation credits and PDF export credits.
- Admin can configure ad placements, reward requirements and feature availability.
- Ads must comply with Google AdMob policies.
- Never promise an ad will appear on every launch; availability and frequency are controlled by the ad network and its policies.

### Default ad configuration

| Setting | Default |
|---|---|
| App Open Ad | Enabled |
| App Open Frequency | Every eligible opening |
| Skip first launch | Enabled |
| Dashboard Native Ad | Enabled |
| Template Gallery Native Ad | Enabled |
| Rewarded Ads | Enabled |
| AI generation reward | 5 completed rewarded ads |
| PDF export reward | 5 completed rewarded ads |
| Watermark | Disabled |
| Paid plans | Disabled |
| Payment system | Disabled |

Admin must be able to change these values.

---

## 4. User Authentication

### Sign up and sign in

- Email and password registration.
- Email and password login.
- Forgot password and reset password.
- Logout.
- Secure password hashing.
- Token-based authentication for Flutter API requests.
- Rate limiting for login and password reset endpoints.

### Guest mode

Users can continue without registering.

Guest users can:
- Create and edit CVs.
- Save drafts.
- Use the same ad reward system.
- Use enabled AI and ATS features.
- Export CVs after completing the required reward flow.

Guest data must not be tied only to temporary device storage. Create a secure guest identity and server-side record. Allow guest account upgrade to a registered account without losing CVs, settings, reward progress or unused credits.

Registered users receive cloud backup and multi-device access.

---

## 5. User App — Main Screens

1. Splash Screen
2. Welcome Screen
3. Login
4. Sign Up
5. Forgot Password
6. Continue as Guest
7. Home Dashboard
8. Template Gallery
9. Template Preview
10. CV Information Form
11. Canva-like CV Editor
12. My CVs
13. CV Preview
14. PDF Export
15. AI Tools
16. ATS Checker
17. Job Description Matcher
18. Notifications
19. Profile
20. Settings
21. Help and Support

### Dashboard

- Welcome header.
- Create New CV.
- My CVs and recent CVs.
- Template Gallery.
- AI Tools.
- ATS Checker.
- Saved Drafts.
- Announcements.
- Clearly labelled native ad placement.
- Profile and settings.

---

## 6. Template Gallery

All templates are free.

### Categories

- Professional
- Modern
- Minimal
- Student
- Fresher
- Experienced
- ATS Friendly
- Creative
- Corporate
- Academic

### Features

- Search and filter.
- Preview.
- Favorites.
- One-column and two-column layouts.
- Multiple pages.
- A4 and Letter page sizes.
- Select and customize.
- Dynamic templates fetched from the backend.
- Admin can publish, unpublish, update and archive templates without requiring an APK update.

---

## 7. CV Information Sections

Support these sections:

- Personal Information: full name, phone, email and address.
- Profile photo.
- Career Objective.
- Professional Summary.
- Education — repeatable entries.
- Work Experience — repeatable entries.
- Skills.
- Projects.
- Certifications.
- Languages.
- Achievements.
- References.
- Custom Sections.

Users must be able to add, edit, remove and reorder repeatable sections.

---

## 8. Canva-like CV Editor

The editor should support:

- Drag and drop.
- Resize and rotate.
- Duplicate and delete.
- Copy and paste.
- Group and ungroup.
- Lock and unlock.
- Layer management.
- Undo and redo.
- Text, image, shape, line, icon and background elements.
- Font family, size, weight and color.
- Text alignment.
- Line height and letter spacing.
- Element spacing.
- A4 and Letter page sizes.
- Page margins and multiple pages.
- Page ordering.
- Zoom.
- Grid, snapping and alignment guides.
- Autosave.
- Live preview.
- PDF preview.

The template JSON schema and Flutter renderer must support the same element properties. Avoid separate, incompatible rendering rules for preview and export.

---

## 9. My CVs

Users can:

- Create a CV.
- Edit a CV.
- Duplicate a CV.
- Rename a CV.
- Delete a CV.
- Change its template.
- View version history.
- Restore an earlier version where supported.
- Use autosave.
- Sync to cloud when registered or securely linked.
- Preview the PDF.
- View export history.

---

## 10. PDF Export

### User features

- High-quality PDF.
- A4 and Letter.
- Multi-page export.
- Selectable text where technically possible.
- Embedded fonts where licensing and technical support permit.
- Print, share and save.
- No watermark.
- Reward-based export unlock.

### Reward flow

Default requirement: 5 completed rewarded ads per export. Admin can configure the number.

1. User requests export.
2. Backend creates or retrieves an export reward session.
3. Flutter loads a rewarded ad.
4. The ad network's server-side verification (SSV) confirms a valid reward.
5. Backend records the reward transaction exactly once.
6. When the required count is reached, the backend grants one export credit.
7. Export credit is reserved when export begins.
8. Consume it only after successful PDF creation.
9. Release the reservation if PDF generation fails.

Do not trust only a Flutter client callback. Use AdMob SSV, unique transaction IDs, signature validation and duplicate-event protection.

---

## 11. AI Generation System

### AI features

1. Career Objective Generator.
2. Professional Summary Generator.
3. Work Experience Bullet Point Generator.
4. Skills Suggestions.
5. Education Description Improver.
6. Project Description Generator.
7. Grammar Correction.
8. CV Content Improvement.
9. Cover Letter Generator.
10. Job Description Keyword Matching.
11. ATS AI Analysis.
12. Language Improvement.

### Per-feature admin settings

- Enable or disable.
- Required rewarded ad count.
- Daily usage limit.
- Provider and model selection.
- Input length limit.
- Output token limit.
- Usage analytics.
- Estimated API cost.

### AI reward logic

Default: 5 completed rewarded ads per AI generation. Admin can configure the count globally and per feature.

1. User chooses an AI feature.
2. User provides the required information.
3. Backend creates a reward session.
4. Flutter displays rewarded ads and progress, for example 2/5.
5. Backend validates each reward through SSV.
6. Backend grants one AI generation credit after the required verified rewards.
7. Reserve the credit when generation starts.
8. Consume it only after successful generation.
9. Release the reservation after a final provider or server failure.

Reward progress must persist across app restarts and account sessions.

### Factual integrity

AI must not invent a user's work history, degree, certification, skill, achievement or other personal claim. Ask for missing information and improve only what the user supplies.

### AI provider management

Initial integration targets:

- OpenAI.
- Google Gemini.
- Anthropic Claude.
- Groq.
- OpenRouter.
- Mistral.
- DeepSeek.
- Together AI.
- Fireworks AI.
- Custom OpenAI-compatible endpoint.

Different providers have different APIs and authentication formats. Implement provider-specific adapters behind a common interface. Do not assume that all providers are interchangeable.

Admin controls:
- Add, edit and remove provider configurations.
- API key add/replace.
- Endpoint and model.
- Enable/disable.
- Priority order.
- Primary and fallback providers.
- Test connection.
- Health status.
- Timeout and retry.
- Rate limits.
- Daily/monthly budgets.
- Usage and estimated cost.
- Token usage.
- Error logs.
- Automatic failover.

API keys must be encrypted at rest and never exposed to Flutter or browser JavaScript. Use environment variables or a secure secret-management approach for encryption keys.

### Failover

- Select the highest-priority enabled and healthy provider.
- On eligible temporary failures (timeout, rate limit, provider unavailable or 5xx), try the next eligible provider within configured limits.
- Use circuit breakers, bounded retries, backoff, idempotency and provider budgets.
- Do not blindly retry invalid credentials, invalid requests or safety-related rejections.
- Log every provider attempt.
- If all providers fail, return a clear error and release the reserved AI credit.

Ads do not guarantee that ad revenue will cover AI API costs. Admin must monitor advertising revenue and AI expenditure.

---

## 12. ATS Checker

Use a rule-based checker as the baseline. It must not require an AI API for basic checks.

### Checks

- Contact information.
- Career summary.
- Work experience.
- Education.
- Skills.
- Keywords.
- Formatting.
- Readability.
- Grammar.
- Job description keyword matching.
- Missing keywords.
- Skills gap.
- Formatting warnings.
- Suggestions.
- Before/after score.

Users can upload a PDF or analyze an existing CV in the app.

A score from 0–100 is an estimated compatibility indicator. It is not a real employer ATS result, hiring guarantee or promise of an interview.

Admin controls:
- Basic checker on/off.
- AI analysis on/off.
- Score weights.
- Supported languages.
- Maximum file size.
- Job matching on/off.
- Usage limits and logs.

Detailed AI analysis may use a rewarded credit and a paid AI API. The basic rule-based analysis should remain available according to admin settings.

---

## 13. PDF-to-JSON Template Importer

### Goal

Admin uploads a normal CV PDF. The backend analyzes it and generates an editable template JSON and preview assets.

### Processing pipeline

1. Admin uploads a PDF.
2. Validate file type, file size, page count and integrity.
3. Preserve the original PDF.
4. Extract text and text positions.
5. Detect page dimensions and orientation.
6. Detect fonts, colors and font weights where possible.
7. Detect shapes, lines, graphics and columns where possible.
8. Detect scanned pages and run OCR if configured.
9. Identify CV sections and dynamic fields.
10. Generate JSON using the official versioned schema.
11. Validate JSON against the schema.
12. Render preview PNG and preview PDF from the generated JSON.
13. Show original and generated previews to admin.
14. Allow manual correction in a Visual Template Builder.
15. Require admin approval before publishing.
16. Publish the template for the Flutter app to fetch.

### Output example

```text
modern_cv_template/
├── original.pdf
├── template.json
├── preview.png
├── preview.pdf
└── assets/
```

Do not permanently extract and store sample profile photos from source PDFs as template assets. Preserve the photo position, dimensions, shape and placeholder in JSON.

### Conversion limitations

PDF conversion cannot be guaranteed to be perfectly accurate. Scanned PDFs, custom fonts, complex columns, vector graphics and unusual layouts may need manual correction. Store processing status, confidence warnings and errors. Admin must be able to retry failed conversions and edit the result.

The preview must be rendered from the generated JSON. Do not simply show the original PDF as if it were the generated template preview.

---

## 14. Shared Default Avatar and Storage Optimization

Use 2–3 shared default avatar assets globally instead of copying an image into every template.

- Templates reference `avatar_01`, `avatar_02` or `avatar_03`.
- If the user uploads a profile photo, use that photo.
- Otherwise show the configured default avatar.
- If neither exists, show a lightweight default icon.
- Admin can configure shared avatar assets.
- User photo is uploaded once and reused across CVs.
- Cache shared assets.
- Prefer optimized WebP images when suitable.
- Never flatten the default photo into the template background.

---

## 15. Django Admin Panel

Build a custom web Admin Panel using Django Templates and Tailwind CSS. Django Admin may also be retained for trusted technical staff, but it is not a replacement for the custom product dashboard.

### Main modules

1. Dashboard.
2. User Management.
3. Guest Management.
4. Template Management.
5. PDF Importer.
6. Visual Template Builder.
7. AI Control Center.
8. AI Provider Management.
9. AI Usage Analytics.
10. Advertisement Management.
11. Reward Management.
12. ATS Settings.
13. Shared Avatar Management.
14. App Settings.
15. Notifications.
16. Maintenance Mode.
17. System Logs.
18. Admin Activity Logs.
19. Storage Management.
20. Backup Management.

### Global admin control

Admin must be able to:
- Enable or disable app features.
- Change feature settings and limits.
- Manage users and guests.
- Publish or unpublish templates.
- Configure PDF import settings.
- Configure AI providers and budgets.
- Configure rewarded ad counts.
- Configure ad placements and ad unit IDs.
- Configure ATS settings.
- Manage shared avatars.
- Send announcements.
- Enable maintenance mode.
- Review logs and backups.

A setting must change backend behavior, not merely hide a Flutter UI element. Enforce permissions and limits on the server. Record configuration changes and admin activity in audit logs.

### Admin security

- Separate admin and user permissions.
- Use Django permissions/groups or a carefully designed role system.
- Protect all admin views and API endpoints.
- Use CSRF protection for browser-based admin forms.
- Use secure cookies and HTTPS in production.
- Require strong passwords and consider MFA for administrators.
- Log sensitive admin actions.
- Never expose provider API keys in frontend HTML or JavaScript.

---

## 16. Backend Architecture

One Django project contains:
- Django-rendered Admin Panel.
- Django REST Framework APIs.
- Authentication and permissions.
- CV and template management.
- Reward and ad verification.
- AI provider routing.
- ATS analysis.
- PDF processing.
- File management.
- Notifications and system settings.

Suggested Django apps:

```text
backend/
├── manage.py
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── accounts/
│   ├── resumes/
│   ├── templates_manager/
│   ├── template_importer/
│   ├── ai_tools/
│   ├── ai_providers/
│   ├── ats_checker/
│   ├── advertisements/
│   ├── rewards/
│   ├── exports/
│   ├── shared_assets/
│   ├── notifications/
│   ├── admin_dashboard/
│   └── system_settings/
├── api/
│   ├── serializers/
│   ├── views/
│   ├── permissions.py
│   └── urls.py
├── templates/
├── static/
├── media/
├── requirements.txt
└── .env.example
```

This is one backend application, not multiple independently deployed backends.

---

## 17. Suggested API Endpoints

All endpoints are served by Django REST Framework. Prefix them with `/api/v1/`.

### Authentication

- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/guest/`
- `POST /api/v1/auth/upgrade-guest/`
- `POST /api/v1/auth/logout/`
- `POST /api/v1/auth/forgot-password/`

### Templates and CVs

- `GET /api/v1/templates/`
- `GET /api/v1/templates/{id}/`
- `POST /api/v1/resumes/`
- `GET /api/v1/resumes/`
- `GET /api/v1/resumes/{id}/`
- `PUT /api/v1/resumes/{id}/`
- `DELETE /api/v1/resumes/{id}/`
- `POST /api/v1/resumes/{id}/export/`

### AI

- `GET /api/v1/ai/config/`
- `GET /api/v1/ai/features/`
- `GET /api/v1/ai/credits/`
- `POST /api/v1/ai/rewards/session/`
- `GET /api/v1/ai/rewards/progress/`
- `POST /api/v1/ai/generate/`
- `GET /api/v1/ai/generations/{id}/`

### Reward verification

- `POST /api/v1/ads/ssv/`

This endpoint must verify the ad network's signed callback and transaction identity. Do not rely on a normal authenticated client request as proof of a rewarded ad.

### ATS

- `POST /api/v1/ats/analyze/`
- `POST /api/v1/ats/job-match/`
- `GET /api/v1/ats/analyses/{id}/`

### Admin APIs (where needed)

- `GET /api/v1/admin/dashboard/`
- `GET /api/v1/admin/users/`
- `GET /api/v1/admin/templates/`
- `POST /api/v1/admin/templates/import-pdf/`
- `GET /api/v1/admin/ai/providers/`
- `POST /api/v1/admin/ai/providers/`
- `PUT /api/v1/admin/ai/providers/{id}/`
- `DELETE /api/v1/admin/ai/providers/{id}/`
- `GET /api/v1/admin/ads/settings/`
- `PUT /api/v1/admin/ads/settings/`
- `GET /api/v1/admin/ats/settings/`
- `PUT /api/v1/admin/ats/settings/`
- `GET /api/v1/admin/settings/`
- `PUT /api/v1/admin/settings/`
- `GET /api/v1/admin/logs/`

Protect every admin endpoint with server-side permission checks and audit logging. The Django-rendered Admin Panel may use internal Django views and forms instead of calling its own REST API for every operation.

---

## 18. Database Design — Main Table Groups

Use Django models and migrations with MySQL.

### Authentication
- users
- guest_accounts (or guest fields in the custom user model)
- password_reset_tokens / Django password reset flow
- authentication tokens

### CV
- resumes
- resume_sections
- resume_versions

### Templates
- templates
- template_versions
- template_categories
- template_assets

### PDF import
- template_import_jobs
- template_import_pages
- template_conversion_elements

### AI
- ai_settings
- ai_features
- ai_providers
- ai_provider_models
- ai_usage_logs
- ai_failover_logs
- ai_cost_stats
- ai_generation_credits
- ai_reward_sessions

### Ads and rewards
- ad_settings
- ad_units
- ad_sessions
- ad_rewards
- export_unlocks
- pdf_exports

### ATS
- ats_analyses
- ats_keywords
- ats_job_descriptions

### Assets and system
- user_assets
- shared_assets
- app_settings
- admin_activity_logs
- notifications
- system_logs

Use foreign keys, indexes, unique transaction IDs, database constraints and atomic transactions. Use soft deletion where appropriate. Prefer Django's built-in user model or a custom user model defined at the beginning of the project; do not change the user model casually after production migrations.

---

## 19. Local Development Setup — Windows + VS Code

### Required software

1. Python — https://www.python.org/downloads/
2. Flutter SDK — https://docs.flutter.dev/install
3. Android Studio — https://developer.android.com/studio
4. MySQL — https://dev.mysql.com/downloads/
5. VS Code — https://code.visualstudio.com/
6. Git — https://git-scm.com/

Tailwind CSS build tooling can use Node.js/npm if the chosen Django Tailwind setup requires it. Node.js is only a frontend asset/build tool here; it is not the backend.

### Project folders

```text
D:\CV-Maker\
├── mobile\
├── backend\
└── docs\
```

### Create Django backend

Open VS Code Terminal:

```powershell
cd D:\CV-Maker

mkdir backend
cd backend

python -m venv venv
venv\Scripts\activate

python -m pip install --upgrade pip
pip install django djangorestframework
pip install mysqlclient pillow pymupdf pdfplumber
pip install python-dotenv
pip freeze > requirements.txt

django-admin startproject config .
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Backend local URL:

`http://127.0.0.1:8000/`

Django built-in admin:

`http://127.0.0.1:8000/admin/`

The custom Tailwind Admin Panel must still be implemented; Django's built-in admin is not automatically the complete product dashboard.

### MySQL setup

1. Start the MySQL server.
2. Create a database, for example `cv_maker`.
3. Create a dedicated database user and grant access only to this database.
4. Configure database connection in Django settings using environment variables.
5. Install and test the MySQL Python driver supported by the selected Windows/Python version.
6. Run:

```powershell
python manage.py makemigrations
python manage.py migrate
```

Example `.env` values (replace placeholders; never commit real secrets):

```env
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=cv_maker
DB_USER=cv_maker_user
DB_PASSWORD=replace-this-password
DB_HOST=127.0.0.1
DB_PORT=3306
```

Do not commit `.env` to Git.

### Flutter setup

Open a separate terminal:

```powershell
cd D:\CV-Maker\mobile
flutter pub get
flutter doctor
flutter devices
flutter run
```

For Android Emulator, the Flutter app reaches the PC backend through:

`http://10.0.2.2:8000/`

For a real phone, use the computer's local network IP address and ensure both devices are on the same network. Configure Django `ALLOWED_HOSTS`, CORS and development network access appropriately. Do not use the emulator address on a physical phone.

### Optional background jobs

Add Celery and Redis when long-running PDF conversion, OCR or AI tasks need background processing.

Typical packages:
- `celery`
- `redis`

Do not add Redis/Celery until the basic Django project and synchronous development flow are working. In production, use a proper worker process and task monitoring.

---

## 20. Security Requirements

- Use HTTPS in production.
- Keep `DEBUG=False` in production.
- Store secrets in environment variables or a secret manager.
- Never expose AI provider keys in Flutter or browser code.
- Enforce ownership checks for every user's CV and files.
- Validate uploaded file type, size, page count and content.
- Store uploads outside executable/static code paths.
- Use safe file names and prevent path traversal.
- Rate-limit authentication, AI and upload endpoints.
- Verify AdMob SSV signatures and transaction IDs.
- Use atomic transactions for rewards and credits.
- Protect admin pages and APIs with permissions.
- Enable CSRF protection for browser admin forms.
- Configure CORS narrowly for trusted origins.
- Maintain backups and test restoration.
- Record security-sensitive admin activity.
- Scan and handle uploaded files safely.

---

## 21. Testing Requirements

### Backend
- Authentication and guest upgrade tests.
- User ownership and permissions tests.
- CV CRUD tests.
- Template publishing tests.
- PDF upload validation tests.
- JSON schema validation tests.
- Reward duplicate transaction tests.
- SSV signature validation tests.
- AI provider timeout/failover tests.
- Credit reserve/consume/release tests.
- ATS analysis tests.
- Admin permissions tests.

### Flutter
- Login and guest flow.
- Template loading.
- CV editor operations.
- Autosave and recovery.
- Reward progress.
- PDF export.
- API error handling.
- Device and network behavior.

### End-to-end
- Admin uploads PDF.
- Backend converts PDF to JSON.
- Admin reviews and publishes template.
- Flutter fetches the published template.
- User creates CV.
- User completes verified reward flow.
- Backend exports PDF.

Never claim a feature is complete until its implementation and tests pass.

---

## 22. Implementation Phases

1. Repository inspection and architecture.
2. Django project, MySQL connection and environment configuration.
3. User authentication and guest mode.
4. Flutter navigation and dashboard.
5. CV data forms and template gallery.
6. Template JSON schema and Flutter renderer.
7. CV editor and autosave.
8. Django Tailwind Admin Panel.
9. Admin template management.
10. PDF-to-JSON importer and preview generation.
11. Shared avatar and asset management.
12. AdMob placements and SSV reward verification.
13. Reward credit and export logic.
14. AI provider adapters and admin configuration.
15. AI failover, budgets and analytics.
16. AI tools.
17. Rule-based ATS checker and optional AI analysis.
18. PDF export and version history.
19. Global settings, notifications and maintenance mode.
20. Security hardening, tests, backup and deployment.

---

## 23. Development Agent Instructions

When using Cursor, Claude, AI Studio or another coding agent:

1. Read this entire PRD before coding.
2. Inspect the existing repository before changing files.
3. Preserve working code; do not overwrite the project blindly.
4. Use only Flutter for the mobile app.
5. Use Python Django as the only application backend.
6. Use Django REST Framework for Flutter APIs.
7. Use Django Templates + Tailwind CSS for the custom Admin Panel.
8. Use MySQL and Django ORM.
9. Keep PDF processing inside the Django project; do not create a separate Python microservice.
10. Do not add Laravel, Express.js, Node.js backend, React Admin Panel or a second backend.
11. Node.js may be used only if needed to compile Tailwind CSS assets.
12. Build real functionality, not static mockups.
13. Implement authentication, permissions, validation and backend enforcement.
14. Keep API keys and secrets server-side.
15. Implement and test features in phases.
16. Provide migrations, seed data, `.env.example`, API documentation and setup instructions.
17. If external credentials are missing, build secure configuration screens and document setup steps. Do not fake successful integrations.
18. Clearly report incomplete features and failed tests.
19. Do not put production secrets in source control.
20. Keep the Flutter app and Django API compatible through documented API contracts.

---

## 24. Final Deliverables

- Flutter Android User App.
- Django Backend.
- Django REST Framework APIs.
- Django + Tailwind CSS Admin Panel.
- MySQL database models and migrations.
- CV editor and JSON template renderer.
- PDF-to-JSON importer.
- Admin Visual Template Builder.
- Shared avatar management.
- AI multi-provider integration and failover.
- Rewarded ads and SSV verification.
- ATS checker.
- PDF export.
- Global admin controls.
- API documentation.
- Local development guide.
- Deployment guide.
- Automated tests.

**Final architecture:** Flutter Mobile App → Django REST API → Django Services → MySQL.  
**Admin architecture:** Browser → Django Templates + Tailwind CSS → Django Views/Services → MySQL.  
**PDF processing:** Django PDF processing modules use Python libraries within the same backend project.

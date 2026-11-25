# CV Maker Pro - REST API Documentation (v1)

Base URL: `{host}/api/v1/`

Auth: JWT bearer tokens (`Authorization: Bearer <access>`). Access
tokens are valid 14 days. Refresh via `POST /auth/login/refresh/`.

Throttling: scoped rates for `auth`, `ai`, `upload` (see
`REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']` in `config/settings/base.py`).

## Auth

| Method | Endpoint | Body | Notes |
|---|---|---|---|
| POST | `/auth/register/` | `{email, password, full_name}` | Returns `{user, access, refresh}` |
| POST | `/auth/login/` | `{email, password}` | Returns `{user, access, refresh}` |
| POST | `/auth/login/refresh/` | `{refresh}` | Returns `{access, refresh}` |
| POST | `/auth/guest/` | `{}` | Creates a guest user with `guest_code`; unusable password. 503 in maintenance mode |
| POST | `/auth/upgrade-guest/` | `{email, password, full_name}` | Converts the current guest to a full account, preserving all FK'd data (resumes, credits) |
| POST | `/auth/logout/` | `{refresh?}` | Blacklists the refresh token |
| POST | `/auth/forgot-password/` | `{email}` | Enumeration-safe: always `{detail}` |
| GET | `/auth/me/` | - | Current user serializer |

## App bootstrap

| GET | `/app/config/` | Returns app settings, maintenance mode, ads config (`rewarded_enabled`, `test_mode`, ad unit ids), reward requirements (`ai`, `export` -> `required_ads`), active announcements. |
|---|---|---|

## Templates

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/templates/` | Published templates only. Filters: `category`, `search`; paginated |
| GET | `/templates/categories/` | Category list |
| GET | `/templates/<id>/` | Full definition (Template JSON schema v1.0) |
| POST | `/templates/<id>/favorite/` | Toggle favorite |

### Template JSON schema v1.0

```json
{
  "schema_version": "1.0",
  "settings": {"page_size": "a4|letter", "margin": 36},
  "pages": [
    {"id": "page_1", "background": "#FFFFFF", "elements": [
      {"id": "...", "type": "text|image|rect|line|ellipse|icon",
       "x": 40, "y": 40, "width": 200, "height": 30, "rotation": 0, "z": 0,
       "locked": false,
       "text": "...", "textProps": {"size": 11, "weight": "bold", "color": "#111827", "align": "left", "line_height": 1.3},
       "dataSource": "static|cv|photo", "field": "full_name|profile_photo|...",
       "defaultImage": "avatar_01", "allowUserUpload": true,
       "fill": "#...", "stroke": "#...", "shape": "circle|rect", "icon": "phone"}
    ]}
  ]
}
```

Geometry is in points, origin at the top-left of the page. `dataSource: cv`
elements resolve from the CV render data; list fields render as bullet lines.
The same schema drives the Flutter renderer, the server PDF renderer and the
importer.

## Resumes

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/resumes/` | List (soft-deleted excluded) |
| POST | `/resumes/` | `{name, template_id, data}` |
| GET | `/resumes/<id>/` | Detail incl. sections |
| PATCH | `/resumes/<id>/` | Autosave (`autosave: true`) or explicit save |
| DELETE | `/resumes/<id>/` | Soft delete |
| POST | `/resumes/<id>/duplicate/` | Deep copy |
| GET | `/resumes/<id>/versions/` | Version snapshots |
| POST | `/resumes/<id>/export/` | Renders the PDF. `402` when no export unlock credit; returns the PDF stream/URL on success; failure -> release of the reserved unlock, `500` semantics |

`data` fields map onto template element `field` values: `full_name`, `phone`,
`email`, `address`, `career_objective`, `professional_summary`, plus repeatable
sections keyed `experience`, `education`, `skills` (list of entry dicts).

## AI

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/ai/config/` | Feature list with `enabled`, `has_credit`, `required_ads` |
| POST | `/ai/rewards/session/` | `{feature}` -> open/reuse rewarded session |
| GET | `/ai/rewards/progress/?feature=` | `{verified_count, required_ads}` |
| POST | `/ai/generate/` | `{feature, input_text, role?}`. `402` no credit, `429` daily limit, `400` disabled/invalid. Reserves a credit, consumes on success, releases on failure |
| GET | `/ai/generations/<id>/` | One generation result |

AI routing: providers by priority with transient-error retry (backoff capped
at 8s), failover to the next provider, immediate stop on credential/input
errors, circuit breaker (3 consecutive failures, 60s cooldown), daily/monthly
budget enforcement. API keys are Fernet-encrypted at rest.

## Ads SSV + Rewards

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/ads/ssv/?...` | AdMob SSV callback. Google's signed query is verified (Ed25519, keys fetched from gstatic). Valid + new transaction -> AdReward; `verified_count` reaches `required_ads` -> credit granted. Duplicate transaction -> rejected + RewardFraudLog. Invalid signature -> `400` |
| POST | `/ads/ssv/` | Same verification for client-forwarded queries |

Reward rules (enforced atomically in `apps/rewards/services.py`):

- AI credits and export unlocks are independent.
- Credits are granted only after `required_ads` verified ads in one session.
- `reserve -> settle(success|failure)` lifecycle, idempotent; failures release
  the reservation back to `available`.

## ATS

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/ats/analyze/` | `{resume_id}` or `{text}` -> `{total_score, section_scores, findings, suggestions, missing_keywords, disclaimer}` |
| POST | `/ats/job-match/` | `{resume_id|text, job_description}` -> adds missing-keyword matching |
| GET | `/ats/analyses/<id>/` | Stored analysis |

Purely rule-based; not a real ATS result (disclaimer included in the response).

## Assets

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/assets/upload/` | User image upload (validated + optimized) |
| GET | `/assets/shared/` | Shared avatars (`avatar_01`..`avatar_03`) |

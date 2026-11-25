# CV Maker Pro - Database Documentation

Engine: MySQL in production (env-driven), SQLite fallback for tests/dev.
Django migrations create the full schema; custom `AUTH_USER_MODEL =
accounts.User` must be defined before the first migration (it is - this project
never changes the user model casually).

## Apps and main tables

### accounts
- `accounts_user` - email-based auth, `is_guest`, `guest_code` (unique, server-side
  guest identity), `is_blocked`, `upgraded_at`.
- `accounts_passwordresetcode` - reset codes with expiry.

### resumes
- `resumes_resume` - `data` JSON, template FK, `deleted_at` (soft delete),
  `autosaved_at`.
- `resumes_resumesection` - repeatable sections (`key`, `data` JSON).
- `resumes_resumeversion` - immutable snapshots on explicit saves.

### templates_manager
- `templates_manager_templatecategory`
- `templates_manager_template` (`draft|published|archived`, created_by)
- `templates_manager_templateversion` - immutable definition JSON (schema v1.0)
- `templates_manager_templateasset`, `templates_manager_favoritetemplate`

### template_importer
- `template_importer_templateimportjob` - status flow
  `uploaded -> processing -> needs_review | failed -> published`
- `template_importer_templateimportpage`, `template_importer_conversionelement`

### ai_providers
- `ai_providers_aiprovider` - adapter, base_url, model, encrypted key
  (`api_key_encrypted`), priority, budgets, breaker fields
  (`healthy`, `consecutive_failures`, `opened_until`)
- `ai_providers_aiproviderhealthlog`, `ai_providers_aifailoverlog`

### ai_tools
- `ai_tools_aifeaturesetting` - per-feature enable, limits, tokens
- `ai_tools_aigeneration` - full generation lifecycle (`pending|succeeded|failed`),
  unique `idempotency_key`
- `ai_tools_aiusagelog`, `ai_tools_aicoststat`

### ats_checker
- `ats_checker_atssettings`, `ats_checker_atsanalysis` (scores + JSON detail)

### advertisements
- `advertisements_adsetting` - singleton ad config incl. SSV public key PEM override
- `advertisements_adrewardrequirement` - per `purpose` (ai|export) `required_ads`
- `advertisements_adsession` (`open|completed|cancelled`)
- `advertisements_adreward` - **unique transaction_id** (fraud protection at the DB level)

### rewards
- `rewards_aigenerationcredit`, `rewards_exportunlock`
  (`available|reserved|consumed`, granted_at, reserved_at, consumed_at)
- `rewards_rewardfraudlog`

### shared_assets
- `shared_assets_sharedasset` (avatar_01..03 keys), `shared_assets_userasset`

### notifications
- `notifications_announcement`, `notifications_notification`

### system_settings
- `system_settings_appsetting` - `get_setting(group, key)` / `set_setting(...)`;
  defaults for maintenance mode, ats enforcement, export limits
- `system_settings_adminactivitylog`, `system_settings_systemlog`

## Integrity and concurrency

- All credit mutations run inside `transaction.atomic` with
  `select_for_update()` row locks.
- Ad reward dedupe rides on the unique constraint of `transaction_id`.
- Soft deletes retain user data while hiding it from queries.
- Foreign keys with `on_delete=CASCADE/PROTECT` per PRD semantics; indexes on
  frequently-filtered columns (`status`, `user`, `created_at`).

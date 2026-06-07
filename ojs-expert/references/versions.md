# OJS Versions, Releases & Official Documentation Map

Verified June 2026 against pkp.sfu.ca/software/ojs/download/, release notebooks, and docs.pkp.sfu.ca. Re-verify "latest" numbers when precision matters — point releases ship regularly.

## Release lines (as of June 2026)

| Line | Latest | Date | PHP | Status |
|---|---|---|---|---|
| 3.3.0-x | 3.3.0-22 | 2025-11-19 | 7.3+ | **Current LTS**, supported ≥ Jan 1 2027 |
| 3.4.0-x | 3.4.0-10 | 2025-11-21 | 8.0+ | Stable; will never be LTS |
| 3.5.0-x | 3.5.0-4 | 2026-04-09 | 8.2.0+ | Current line; designated next LTS (designation pending) |
| 3.6 | unreleased | "2026" | n/a | Non-LTS; continuous publication, preprints (AO→VoR versioning), EC/ORE-funded |

LTS rule: once a 3.5.x gets the LTS designation, 3.3 and 3.4 enter a one-year EOL countdown. OJS releases are announced on pkp.sfu.ca; security advisories via the PKP forum Announcements category and `github.com/pkp/ojs/security`. PKP does not use GitHub Releases — use the download page or `stable-3_x_0` branches/tags.

## What changed in each version (developer/admin lens)

**3.3 (Feb 2021)**: ADODB→Laravel DB began; Guzzle; "BLIND"→"ANONYMOUS" review constants; plugin files `.inc.php`, `HookRegistry`, `import()` — the legacy conventions.

**3.4 (May 2023)**: PHP 8.0+; namespaces mandatory (`APP\`/`PKP\`); `Hook::add` replaces `HookRegistry`; Services→`Repo::` repositories; class constants replace global defines; locale codes shortened (`en_US`→`en`); UTF-8 mandatory; Laravel Mailer + **Mailables** (PHPMailer gone); **jobs/queues**; REST-based submission wizard; core **DOI management** (plugin retired); COUNTER R5 stats engine; `time_zone` + `allowed_hosts` config; only `mysqli`/`postgres9` drivers.

**3.5 (Jun 16 2025)**: PHP 8.2+; Vue 2→**Vue 3** (Composition API; ListPanel→Table; Tailwind); **Eloquent ORM** adoption; **Slim→Laravel API routing** (`APIHandler::endpoints` hook removed); **Laravel Task Scheduler** (Acron plugin removed; `tools/runScheduledTasks.php`→`lib/pkp/tools/scheduler.php`; new `[schedule]` config); `app_key` (Laravel APP_KEY; `lib/pkp/tools/appKey.php`); non-namespaced / `.inc.php` plugins unsupported; `fatalError()` removed; Stringy→`Str`; new plugin-settings pattern (PluginSettingsController + FormComponent + VueModal); **ORCID in core**; GDPR-friendly user invitation workflow; redesigned editorial dashboard; in-workflow **JATS** support (file stage 21); ALTCHA captcha option; dashboard/email/ORCID API endpoints.

**3.6 (announced, 2026)**: continuous publication (publish articles without issues), preprints/"author originals" with AO→VoR upgrade path. No release notebook yet — do not state 3.6 specifics as fact.

## Official documentation map (docs.pkp.sfu.ca)

Developer:
- **Dev hub**: `/dev/` · **Dev Documentation**: `/dev/documentation/en/` (en = 3.5; `/dev/documentation/3.4/en/`, `/3.3/` exist)
- **Plugin Guide**: `/dev/plugin-guide/en/` · **Theming Guide**: `/pkp-theming-guide/en/` (legacy slug — `/dev/theming-guide/` does not exist)
- **REST API reference**: `/dev/api/ojs/3.4` (3.4 only; for 3.5 read `docs/dev/swagger-source.json` on `stable-3_5_0`)
- **Release notebooks**: `/dev/release-notebooks/en/` (3.2–3.5) · **Upgrade guide**: `/dev/upgrade-guide/en/`
- **UI Library**: `/dev/ui-library` · Source: `github.com/pkp/ojs`, `github.com/pkp/pkp-lib`, `github.com/pkp/pluginTemplate` (branch `main` = 3.5 pattern, `stable-3_4_0` = 3.4 pattern)

Admin / editorial:
- **Admin Guide**: `/admin-guide/en/` · **Learning OJS**: `/learning-ojs/` (default = 3.5; `/learning-ojs/3.4/en/`, `/3.3/en/`)
- **Crossref manual**: `/crossref-ojs-manual/en/` · **DOI plugin guide** (3.0–3.3 only!): `/doi-plugin/` · **ORCID**: `/orcid/` · **ROR**: `/ror-plugin/en` · **iThenticate**: `/ithenticate/en`
- **PKP PN**: `/pkp-pn/en/` · **Google Scholar**: `/google-scholar/` · **DOAJ**: `/doaj/` · **Indexing guide**: `/indexing-guide/en/`
- **QuickSubmit (back issues)**: `/quicksubmit/en/` · **GDPR**: `/gdpr/en` · **Multilingual guide**: `/multiling-guide/en/` · **Translating guide**: `/translating-guide/en/`
- Getting Found Staying Found `/getting-found-staying-found/en/` · Metadata practices `/metadata-practices/en/` · Designing Your Journal `/designing-your-journal/en/` · Starting a journal `/starting-a-journal/en/` · Plugin inventory `/plugin-inventory/en/` · FAQ `/faq/en/`

Support: PKP Community Forum `forum.pkp.sfu.ca` (the de-facto knowledge base for error messages — search it when troubleshooting unusual errors).

## Picking advice per version — quick matrix

| Topic | 3.3 | 3.4 | 3.5 |
|---|---|---|---|
| Plugin class file | `XPlugin.inc.php`, no namespace | `XPlugin.php` + namespace (+ optional alias) | `XPlugin.php` + namespace only |
| Hooks | `HookRegistry::register` | `Hook::add` | `Hook::add` (several hooks removed) |
| Plugin settings UI | Smarty Form/AjaxModal | Smarty Form/AjaxModal | Controller + FormComponent + VueModal |
| Entities | DAOs/Services | `Repo::` facades | `Repo::` + Eloquent |
| Scheduled tasks | Acron / runScheduledTasks.php | Acron / `scheduled_tasks` | `scheduler.php` / `[schedule]` |
| Jobs | — | jobs.php / job_runner | same + `process_jobs_at_task_scheduler` |
| DOI | DOI plugin | core DOI system | core + DOI search |
| ORCID | plugin | plugin | core |
| Locale dirs | `en_US` | `en` | `en` |

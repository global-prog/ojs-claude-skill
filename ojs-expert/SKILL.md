---
name: ojs-expert
description: Comprehensive expertise for OJS (Open Journal Systems) by PKP, targeting 3.4.x/3.5.x. This skill should be used when developing OJS/PKP plugins or themes, calling the OJS REST API or OAI-PMH endpoints, installing/upgrading/administering an OJS server, troubleshooting OJS errors, or configuring journals, editorial workflows, DOIs/Crossref, ORCID, or statistics. Triggers include any mention of OJS, Open Journal Systems, PKP, pkp-lib, journal publishing platform work, or files like config.inc.php and version.xml.
---

# OJS Expert

Expert knowledge for working with OJS (Open Journal Systems), the scholarly journal publishing platform by PKP (Public Knowledge Project). Covers OJS 3.4.x and 3.5.x in depth, with 3.3 differences noted where relevant. All reference material in this skill was verified against official PKP documentation (docs.pkp.sfu.ca) and the `pkp/ojs` + `pkp/pkp-lib` source (branches `stable-3_4_0` / `stable-3_5_0`).

## Before doing anything: identify the version

OJS versions differ substantially (3.3 → 3.4 → 3.5 each changed plugin conventions, APIs, and admin tooling). Never give version-blind advice. Detect the version of the target install first:

- **From the codebase:** read `dbscripts/xml/version.xml` in the OJS root (contains `<release>`), or check the `versions` table in the DB (`SELECT * FROM versions WHERE current = 1`).
- **From a live site:** Administration → System Information (admin login), or `GET <base>/api/v1/site` with an admin token.
- **Quick paper test:** `lib/pkp/tools/scheduler.php` exists → 3.5+; `Hook.php` in `lib/pkp/classes/plugins/` → 3.4+; plugin classes ending `.inc.php` → 3.3-era code.

Version cheat-sheet (as of June 2026): **3.3.0-x** = current LTS (PHP 7.3+, supported ≥ Jan 2027) · **3.4.0-x** = stable, never LTS (PHP 8.0+) · **3.5.0-x** = current line, next LTS (PHP 8.2+) · **3.6** = unreleased, expected 2026 (continuous publication, preprints). Details: `references/versions.md`.

## Core conventions (3.4+) that must never be violated

1. **Namespaces, not `import()`**: `use APP\facades\Repo;` / `use PKP\plugins\Hook;`. The legacy `import('classes...')` is 3.3-only. In 3.5, non-namespaced plugins and `.inc.php` class files **do not load at all**.
2. **Hooks**: `Hook::add('Name', $callback)` (class `PKP\plugins\Hook`), callback returns `Hook::CONTINUE` (false) or `Hook::ABORT` (true). `HookRegistry::register()` is the deprecated 3.3 form.
3. **Entities via Repo facades**: `Repo::submission()->get($id)`, `Repo::publication()`, `Repo::user()`, with fluent Collectors for queries (`Repo::submission()->getCollector()->filterByContextIds([$id])->getMany()`). Direct DAO access bypasses hooks/side-effects — only for bulk operations.
4. **Class constants, not globals**: `Submission::STATUS_PUBLISHED`, `Role::ROLE_ID_MANAGER`. Verified integer values for every constant group (roles, stages, statuses, file stages, decisions, DOI statuses) are in `references/constants.md` — never guess these integers.
5. **Locale codes are short** since 3.4: `locale/en`, not `locale/en_US`. Multilingual data is always locale-keyed JSON: `{"title": {"en": "..."}}`.
6. **Version numbers are four-part** everywhere (plugins, gallery): `1.0.0.0`.

## Working against a live install

- Read `config.inc.php` first — it tells you the DB, `files_dir`, `base_url`, `restful_urls` (whether URLs need `index.php/`), email setup, and job/scheduler mode. Never commit or echo its secrets (`salt`, `api_key_secret`, DB password, `app_key`).
- **Back up before destructive operations** (upgrade, plugin install, DB changes): `mysqldump` the DB + tar `files_dir` + copy `config.inc.php` and `public/`.
- After changing templates, locales, or plugin settings XML, clear caches: delete contents of `cache/t_compile/`, `cache/t_cache/`, `cache/_db/` (or UI: Administration → Clear Template Cache / Clear Data Caches).
- Long-running work (emails, stats, DOI deposits) runs through **Laravel queue jobs** — if something "doesn't happen", check jobs first: `php lib/pkp/tools/jobs.php list` / `failed`. See `references/admin-operations.md`.
- Windows host note: OJS CLI tools are PHP scripts — invoke as `php tools/upgrade.php check` from the OJS root regardless of OS.

## Task routing

Load the matching reference before answering non-trivial questions — they contain verified signatures, endpoint inventories, exact commands, and 3.4↔3.5 differences:

| Task | Reference |
|---|---|
| Build/modify a plugin (any category), migrations, scheduled tasks/jobs from plugins, distribution | `references/plugin-development.md` |
| Find/use a specific hook — verified names, arguments, ABORT semantics, removed-in-3.5 list | `references/hooks-catalog.md` |
| Vue form fields (`Field*` classes), FormComponent API, custom handlers, authorization policies, file storage, validation | `references/ui-forms-handlers.md` |
| Build/modify a theme, child themes, LESS variables, override frontend templates | `references/theme-development.md` |
| Call the REST API, API auth/tokens, OAI-PMH harvesting, COUNTER SUSHI | `references/rest-api.md` |
| Integer constants for API params & code (roles, stages, statuses, decisions…) | `references/constants.md` |
| Install, configure (`config.inc.php`), upgrade, jobs/scheduler, CLI tools, security hardening, troubleshooting | `references/admin-operations.md` |
| Journal settings, roles, workflow stages/decisions, review process, publishing, DOIs/Crossref, ORCID, emails, stats | `references/editorial-workflow.md` |
| Codebase architecture: Repo pattern, schemas, routers, request lifecycle, directory layout | `references/architecture.md` |
| Version differences, release history, LTS/support status, official docs map | `references/versions.md` |

## REST API quick access

Use `scripts/ojs_api.py` (stdlib-only Python) for ad-hoc API calls against a live install instead of hand-writing HTTP code:

```bash
# Token: user profile → API Key (requires api_key_secret set in config.inc.php)
python scripts/ojs_api.py --base "https://example.com/index.php/journalpath" --token "$TOKEN" GET submissions -p status=1 -p count=20
python scripts/ojs_api.py --base "..." --token "..." PUT submissions/12/publications/14/publish
python scripts/ojs_api.py --base "..." --token "..." GET issues --all   # auto-paginate
```

Run `python scripts/ojs_api.py --help` for full usage. For one-off calls, plain curl with `Authorization: Bearer <token>` works equally well (examples in `references/rest-api.md`).

## Answering style for OJS work

- State which OJS version an answer applies to; flag where 3.4 and 3.5 diverge (plugin settings UI, scheduler, API routing are the big three).
- Prefer official mechanisms (hooks, child themes, template overrides, plugin settings) over core-file edits — core edits are lost on upgrade.
- When the user's install is reachable, verify claims against it (read actual source under `lib/pkp/`, check actual config) rather than relying on memory — patch releases change details.
- For facts not covered by the references (rare plugin categories, third-party plugins), check the live source or docs.pkp.sfu.ca rather than guessing; the references note which few items remain unverified.

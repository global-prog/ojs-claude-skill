# OJS Internal Architecture (3.4+ with 3.5 deltas)

Verified against PKP Dev Documentation (docs.pkp.sfu.ca/dev/documentation/en/ — `en` currently documents 3.5; 3.4/3.3 variants exist) and pkp-lib source.

## 1. Directory layout of an install

```
ojs/
├── index.php                 # front controller
├── config.inc.php            # the one config file
├── classes/                  # APP\* classes (OJS-specific entities, e.g. issue, journal)
├── lib/pkp/                  # the shared PKP library (PKP\* classes, shared templates, tools)
│   ├── classes/              # core: plugins/, security/, submission/, db/, core/…
│   ├── templates/            # shared Smarty templates (frontend + backend)
│   └── tools/                # shared CLI tools (jobs.php, scheduler.php…)
├── api/v1/                   # REST API controllers (app-specific)
├── pages/                    # page handlers for PageRouter
├── controllers/              # component handlers (grids, modals)
├── plugins/<category>/<name>/
├── templates/                # app Smarty templates (override lib/pkp/templates)
├── schemas/                  # entity JSON schemas (app-level overrides/additions)
├── locale/<lang>/*.po        # short locale codes since 3.4
├── dbscripts/xml/version.xml # install version
├── cache/                    # t_compile, t_cache, _db… (safe to clear)
└── public/                   # web-accessible uploads (logos, etc.)
```

`files_dir` (submission files, scheduled-task logs) lives **outside** this tree.

## 2. Laravel integration

- 3.4: Laravel container/facades, Laravel Mailer (Symfony transport), queues/jobs, query builder available; namespaces mandatory; `Hook` replaces `HookRegistry`.
- 3.5: ADODB fully removed → Laravel DB layer; Pimple → Laravel Service Container; Slim → Laravel API routing; many entities now **Eloquent models** (Announcements, UserGroups, Notifications, StageAssignments, …; `ReviewAssignmentDAO` removed); Laravel Task Scheduler; `app_key` (APP_KEY) in config; Vue 3 + Tailwind in the editorial UI.

## 3. Entities: DataObject → Schema → DAO → Repository

Per major entity (e.g. `Publication`): a `DataObject` class (`getData`/`setData`, no DB access), a JSON **schema** defining properties (`"multilingual": true` for localized props), a `DAO` (persistence only), and a `Repository` (public API + side effects: hooks, logs, emails, jobs). Optional fluent `Collector` for queries.

```php
use APP\facades\Repo;

$submission = Repo::submission()->get($id);                       // by id
$user = Repo::user()->getByUsername($username);
$submissions = Repo::submission()->getCollector()
    ->filterByContextIds([$contextId])
    ->filterByStatus([Submission::STATUS_PUBLISHED])
    ->getMany();                                                   // LazyCollection
Repo::publication()->edit($publication, ['title' => ['en' => 'New']]);
```

Available repos (3.4+): `submission()`, `publication()`, `user()`, `author()`, `institution()`, `issue()` (OJS app), `galley()`, `emailTemplate()`, `doi()`, `category()`, `announcement()` (Eloquent in 3.5), and more — check `lib/pkp/classes/facades/Repo.php` + `classes/facades/Repo.php` in the live install.

Schema inventory (3.5): OJS `schemas/`: context, galley, issue, publication, section, submission. pkp-lib `schemas/`: affiliation, announcement, author, category, context, decision, doi, emailLog, emailTemplate, eventLog, highlight, institution, publication, reviewAssignment, reviewRound, ror, section, site, submission, submissionFile, user, userGroup. (App schemas extend/override same-named lib schemas.)

Custom fields: hook `Schema::get::<entity>` to add properties; they persist automatically in the entity's settings table and surface in the API.

## 4. Database conventions

- Two-table pattern per entity: main table (`journals`) + settings table (`journal_settings`) holding key/value rows with a `locale` column; arrays/objects JSON-serialized in settings values (not efficiently searchable).
- Migrations: Laravel-style migration classes (see `lib/pkp/tools/migration.php`, plugin migrations via `Plugin::getInstallMigration()`).
- Version registry: `versions` table (`current = 1` row per product).

## 5. Request lifecycle & routing

`index.php` → `PKPRequest` → router selection:
- **PageRouter** — public/backend pages: `/<journal>/<page>/<op>/<args>`; handler at `pages/<page>/index.php` (falls back to `lib/pkp/pages/`); op = public method `$handler->$op($args, $request)`.
- **APIRouter** — `/<journal>/api/v1/<resource>`; controllers under `api/v1/<resource>/`; Laravel routing in 3.5 (`PKPBaseController::getGroupRoutes()`), Slim-style handlers in 3.4.
- **PKPComponentRouter** — AJAX component grids: class PascalCase → kebab-case URL (`BackIssueGridHandler` → `grid.issues.BackIssueGridHandler`), under `controllers/`.

Always build URLs through the dispatcher, never by hand:
```php
$request->getDispatcher()->url($request, Application::ROUTE_PAGE, null, 'issue', 'view', [$issueId]);
```

## 6. TemplateManager & UI

- Frontend + (3.4) backend rendered with **Smarty 3**: `TemplateManager::getManager($request)` → `assign()`, `display()`, `fetch()`. Compiled templates cached in `cache/t_compile/`.
- Backend editorial UI: Vue (2 in 3.4, **3 in 3.5** — Composition API, Pinia-style composables, Tailwind, new `Table` component; `ListPanel` deprecated). UI library docs: docs.pkp.sfu.ca/dev/ui-library.
- State handed to Vue via `setState`/templates; in 3.5 don't pass translations as props (use the i18n composable).

## 7. Where to find things fast (live install)

| Looking for | Location |
|---|---|
| A hook's call sites | `grep -r "Hook::call" lib/pkp/ classes/ pages/` |
| Entity properties | `schemas/*.json` + `lib/pkp/schemas/*.json` |
| REST controllers | `api/v1/` + `lib/pkp/api/v1/` |
| Mailables | `lib/pkp/classes/mail/mailables/`, `classes/mail/mailables/` |
| Decision types | `lib/pkp/classes/decision/types/` |
| Form components | `lib/pkp/classes/components/forms/` |
| Queue jobs | `lib/pkp/jobs/`, `classes/jobs/` |
| Locale strings | `locale/<lang>/*.po`, `lib/pkp/locale/<lang>/*.po` |
| Config reference | `config.TEMPLATE.inc.php` of the same release |

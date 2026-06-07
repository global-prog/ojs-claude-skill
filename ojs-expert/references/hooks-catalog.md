# OJS Hooks Catalog (3.4 / 3.5) — verified at call sites

Every entry verified by reading the actual `Hook::call(...)` / `Hook::run(...)` call site in `pkp/pkp-lib` / `pkp/ojs` on `stable-3_5_0`. To discover more hooks on a live install: `grep -r "Hook::call\|Hook::run" lib/pkp/classes classes pages` (3.3: `HookRegistry::call`). Official (incomplete) list: docs.pkp.sfu.ca/dev/documentation/en/utilities-hooks.

## 1. Engine semantics (`PKP\plugins\Hook`)

- Callback: `function ($hookName, $args)`; dispatch stops at the first callback returning `Hook::ABORT` (true).
- **ABORT only matters when the call site checks the return** — pattern `if (!Hook::call(...)) { default code }` means ABORT skips the default (plugin takes over). A bare `Hook::call(...)` is notification-only; mutate by-reference args instead.
- Sequence: `Hook::add($name, $cb, Hook::SEQUENCE_CORE|SEQUENCE_NORMAL|SEQUENCE_LATE|SEQUENCE_LAST)`.
- 3.5 registers removed-hook names via `Hook::addUnsupportedHooks()` → deprecation warning if a plugin adds them (§10).
- Hooks are reliable only from **generic** plugins (loaded every request).

## 2. Routing / handlers

| Hook | Args | ABORT checked? | Use |
|---|---|---|---|
| `LoadHandler` (PKPPageRouter::route) | `[&$page, &$op, &$sourceFile, &$handler]` | yes | claim a page URL: set `$handler`, return ABORT |
| `LoadComponentHandler` (PKPComponentRouter) | `[&$component, &$op, &$componentInstance]` | yes | supply a grid/component handler |
| `APIHandler::endpoints::{entity}` (3.5; APIHandler) | `[$controller, $apiHandler]` (mutable objects) | no | add/override REST routes; e.g. `…::submissions`, `…::plugin` for `registerPluginApiControllers` |
| `Dispatcher::dispatch` | `[$request]` | no | earliest per-request hook |
| `PKPPageRouter::url` | assoc by-ref incl. `&$result` | yes | rewrite generated URLs |
| `PKPApplication::execute::catch` (3.5) | `['throwable' => $t]` | yes | custom top-level error handling |

## 3. Templates

Mechanism: `{call_hook name="Templates::X::Y"}` in any `.tpl` fires `Hook::call($name, [&$params, $smarty, &$output])` — **append HTML to `$args[2]` (`&$output`)** and it renders at that spot. Extra tpl attributes arrive in `$args[0]`.

| Hook | Args | ABORT checked? | Use |
|---|---|---|---|
| `TemplateManager::display` | `[$templateMgr, &$template, &$output]` | yes | inspect/assign before render; ABORT to replace whole page (`&$output`) |
| `TemplateManager::fetch` | `[$templateMgr, $template, $cache_id, $compile_id, &$result]` | yes | substitute a rendered template |
| `TemplateResource::getFilename` | `[&$filePath, $template]` | no | redirect template path (powers `_overridePluginTemplates`) |
| `TemplateManager::setupBackendPage` | `[]` | no | add nav/state to backend pages |
| `PageHandler::compileLess` | `[&$less, &$lessFile, &$args, $name, $request]` | no | inject LESS at compile |

Verified `Templates::*` injection points (grep `call_hook` in templates for the full set): `Templates::Article::Main`, `Templates::Article::Details`, `Templates::Article::Details::Reference` (gets `citation=`), `Templates::Article::Footer::PageFooter`, `Templates::Issue::Issue::Article`, `Templates::Index::journal`, `Templates::Common::Sidebar`, `Templates::Common::Footer::PageFooter`.

Reading template data in a `TemplateManager::display` callback: guard on `$args[1] === 'frontend/pages/issue.tpl'`, then `$templateMgr->getTemplateVars('issue')`, `assign()`, return CONTINUE.

## 4. Schema / forms (the custom-field machinery)

| Hook | Args | Use |
|---|---|---|
| `Schema::get::{entity}` (PKPSchemaService::get) | `[&$schema]` | add properties: `$schema->properties->myField = (object)['type'=>'string','multilingual'=>true,'apiSummary'=>true,'validation'=>['nullable']];` Entities: publication, submission, context, user, issue, galley, author, … |
| `Schema::get::before::{entity}` (3.5) | `[&$forceReload]` | force schema cache reload |
| `Form::config::before` (FormComponent::getConfig) | `[$form]` | add/remove fields — guard on `$form->id` |
| `Form::config::after` | `[&$config, $form]` | mutate the final config array |
| `{entity}::validate` (Repository::validate) | `[&$errors, $entity, $props, $allowedLocales, $primaryLocale]` | add validation errors |
| `Submission::validateSubmit` | `[&$errors, $submission, $context]` | validate at author submit |

## 5. Entity lifecycle (Repository hooks — EntityDAO fires NO hooks)

Convention: `Entity::add`, `Entity::edit`, `Entity::delete::before`, `Entity::delete` (+ extras). None check ABORT.

- **Submission**: `Submission::add` `[$submission]` · `Submission::edit` `[$new, $old, $params]` · `Submission::delete::before`/`::delete` · `Submission::updateStatus` `[&$newStatus, $status, $submission]`
- **Publication**: `Publication::add` `[&$publication]` · `Publication::edit` `[&$new, $old, $params, $request]` · `Publication::version` `[&$new, $old]` (copy custom fields here!) · `Publication::publish::before` `[&$new, $old]` · `Publication::publish` `[&$new, $old, $submission]` (trigger DOI/indexing here) · `Publication::unpublish[::before]` · `Publication::delete[::before]` · `Publication::validatePublish`
- **User**: `User::add` `[$user]` (≈ registration hook — there is no dedicated registration hook) · `User::edit` · `User::delete[::before]` · `UserAction::mergeUsers` `[&$oldId, &$newId]`
- Collector queries: `{entity}::Collector` convention (query-builder customization).

Legacy DAO hooks still firing in 3.5 (`PKP\db\DAO`): `{dao}::getAdditionalFieldNames` `[$dao, &$fields]` — the supported way to persist extra settings for legacy-DAO entities (e.g. `articlegalleydao::getAdditionalFieldNames`); `{dao}::getLocaleFieldNames`; low-level `{dao}::_{method}` SQL hooks `[&$sql, &$params, &$value]` (ABORT-checked). The `*DAO::_fromRow` family is removed in 3.5.

## 6. Email

- 3.5: `Email::send::before` (Mailer::sendSymfonyMessage) — `['message' => $symfonyMessage, 'mailer' => $mailer]`, not checked. Inspect/modify before transport.
- 3.4: no such hook — use Laravel events `MessageSendingFromContext` / `MessageSendingFromSite`.
- `Mailer::Mailables` (mail Repository::getMany) — `[$mailables(Collection), $context]`: register a plugin's custom Mailable class so it appears in the email-templates UI.
- `EmailTemplate::restoreDefaults`.
- **`Mail::send` is REMOVED in 3.5.**

## 7. Article / issue / galley delivery (pkp/ojs)

| Hook | Args | ABORT checked? | Use |
|---|---|---|---|
| `ArticleHandler::view` | `[&$request, &$issue, &$article, $publication]` | yes | take over article landing page; inject template data (citationStyleLanguage pattern) |
| `ArticleHandler::view::galley` | `[&$request, &$issue, &$galley, &$article, $publication]` | yes | custom galley viewers (PDF.js etc.) |
| `ArticleHandler::download` | `[$article, &$galley, &$submissionFileId]` | yes | gate/serve downloads (paywalls, counters) |
| `IssueHandler::view::galley` / `IssueHandler::download` | `[&$request, &$issue, &$galley]` / `[&$issue, &$galley]` | yes | issue-galley equivalents |
| `FileManager::downloadFileFinished` | `[&$returner]` | no | after-send notification |

## 8. Search indexing (pkp/ojs `ArticleSearchIndex`) — replaceable by external engines

ABORT-checked (plugin can fully replace SQL indexing): `ArticleSearchIndex::articleMetadataChanged` `[$submission]` · `::submissionFileChanged` `[$articleId, $type, $submissionFileId]` · `::submissionFilesChanged` `[$article]` · `::submissionFileDeleted` · `::rebuildIndex` `[$log, $journal, $switches]`. Notification-only: `::articleDeleted`, `::articleChangesFinished`.

## 9. OAI & misc

- `OAI::metadataFormats` `[$namesOnly, $identifier, &$formats]` — register OAI formats (behind OAIMetadataFormatPlugin).
- `OAIDAO::getJournalSets` `[$dao, $journalId, $offset, $limit, $total, &$sets]` — add OAI sets.
- `Decision::types` `[$collection]` + `Workflow::Decisions` `[$decisions, $stageId]` — add/remove/replace editorial decisions.
- `Request::<property>` (e.g. `Request::getBaseUrl`), `API::<endpoint>::params` (e.g. `API::context::params`).
- `GoogleScholarPlugin::references` — example of a plugin exposing its own hook for others.
- **Navigation menus** (`PKPNavigationMenuService`): `NavigationMenus::itemTypes` `[&$types]` (add custom NMI types: `$types['NMI_TYPE_X'] = ['title'=>…, 'description'=>…]`) · `NavigationMenus::itemCustomTemplates` `[&$templates]` · `NavigationMenus::displaySettings` `[$navigationMenuItem, $navigationMenu]` (visibility/URL at render time).
- **Backend settings-tab injection**: `Template::Settings::website` (also `::context`, `::distribution` variants) — append a tab: `$output .= $templateMgr->fetch($this->getTemplateResource('myTab.tpl'))` (verified: staticPages).
- **Legacy form lifecycle** (`issueform` example, used by the Immersion theme): `issueform::display`, `::initdata`, `::readuservars`, `::execute` — extend backend Smarty/FBV forms end-to-end.
- `Templates::Common::Sidebar` — in 3.5 PKPTemplateManager registers its own `displaySidebar()` here, rendering enabled block plugins from the context/site `sidebar` setting (see frontend-templating.md §4); your callback can append additional sidebar HTML.

## 10. Removed in 3.5 (deprecation warning if registered)

`APIHandler::endpoints` · `Mail::send` · `API::_submissions::params` · `Template::Workflow` · `Template::Workflow::Publication` · `Workflow::Recommendations` · `SubmissionHandler::saveSubmit` · `PluginGridHandler::plugin` · `EditorAction::modifyDecisionOptions` · `EditorAction::recordDecision` · `SubmissionFile::assignedFileStages` · `AcronPlugin::parseCronTab` · `CitationDAO::afterImportCitations` · `Announcement::delete[::before]` · `Announcement::Collector` · `UserGroup::delete[::before]` · all `*::getProperties` hooks · all `*::getMany::queryBuilder`/`::queryObject` hooks · all `*DAO::_fromRow`/`_returnXFromRow` hooks · `PKPLocale::*` hooks · `API::stats::publication*::params` variants.

Added in 3.5: `APIHandler::endpoints::{entity}`, `Email::send::before`, `Form::config::before/after`, `Mailer::Mailables`, `Schema::get::before::{schema}`, `PKPApplication::execute::catch`.

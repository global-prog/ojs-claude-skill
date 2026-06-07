# OJS UI Forms, Field Classes, Handlers, Authorization, Files, Validation (3.4/3.5)

Verified against pkp-lib source (`classes/components/forms`, `classes/security/authorization`) and PKP dev docs (forms, handlers, authorization, files, validation chapters). Used by plugin settings forms, theme options, custom fields, and custom handlers.

## 1. FormComponent API (`PKP\components\forms\FormComponent`)

Props: `$id`, `$method` ('POST'/'PUT'), `$action`, `$locales`, `$fields`, `$groups`, `$hiddenFields`, `$pages`, `$errors`. Constant `FormComponent::ACTION_EMIT = 'emit'` (client-side only). Position constants (global): `FIELD_POSITION_BEFORE` / `FIELD_POSITION_AFTER`.

```php
$form = new MyForm($id, $method, $action, $locales);
$form->addField(new FieldText('name', [...]))                       // append
     ->addField(new FieldText('abbr', [...]), [FIELD_POSITION_AFTER, 'name'])
     ->removeField('subjects')
     ->addGroup(['id' => 'identity', 'label' => __('…')])           // fields get 'groupId' => 'identity'
     ->addPage(['id' => 'p1', 'submitButton' => ['label' => __('common.save')]])
     ->addHiddenField('csrf', $token);
$config = $form->getConfig();   // fires Form::config::before then Form::config::after hooks
```

Render flow (page handlers): `$templateMgr->setState(['components' => [FORM_X => $form->getConfig()]])` → template `<pkp-form v-bind="components.{$smarty.const.FORM_X}" @set="set" />`. Locales come from `$context->getSupportedFormLocaleNames()` (most forms) or `getSupportedSubmissionLocaleNames()`.

Common Field args: `label`, `description`, `tooltip`, `groupId`, `isRequired`, `isMultilingual`, `value`, `default`, `showWhen` (`'settingName'` truthy, or `['settingName', 'exactValue']`).

## 2. Field class inventory (`PKP\components\forms\Field*`)

In both 3.4 and 3.5:

| Class | Purpose / notable args |
|---|---|
| `FieldText` | text input; `inputType`, `size`, `prefix`, `optIntoEdit` |
| `FieldTextarea` | plain multiline; `size` |
| `FieldRichTextarea` | TinyMCE; `plugins` (default `['link']`), `toolbar`, `uploadUrl`, `wordLimit`, `init` |
| `FieldRichText` | rich single-line |
| `FieldPreparedContent` | rich editor + insertable snippets (`preparedContent`) |
| `FieldSelect` | dropdown; `options` = `[['value'=>…, 'label'=>…], …]` |
| `FieldOptions` | checkboxes/radios; `type` ('checkbox'/'radio'), `options`, `isOrderable` |
| `FieldRadioInput` | radios where one option is free text |
| `FieldColor` | color picker |
| `FieldHTML` | static HTML, no value (`isInert`) |
| `FieldUpload` | dropzone upload; `options['url']` REQUIRED (point at `<api>/temporaryFiles`), `acceptedFiles`, `maxFilesize` |
| `FieldUploadImage` | image upload; `baseUrl`, `altTextLabel`; not usable as a theme option |
| `FieldMetadataSetting` | metadata enable/request/require triplet |
| `FieldControlledVocab` | autosuggest backed by controlled vocab (keywords) |
| `FieldBaseAutosuggest` / `FieldAutosuggestPreset` | type-ahead bases |
| `FieldSelectSubmissions` / `FieldSelectUsers` | entity pickers |
| `FieldPubId` | pub-id generator field |

3.5-only: `FieldAffiliations` (ROR-backed author affiliations), `FieldOrcid`, `FieldSlider` (`min`, `max`, `step`, labels).

Theme options accept any Field except `FieldUpload`/`FieldUploadImage` (see theme-development.md).

## 3. Handlers

**Page handlers** extend `APP\handler\Handler` (or `PKP\controllers\page\PageHandler` from plugins): one public method per op, `op(array $args, Request $request)`, render via TemplateManager; `index()` = op-less URL; 404 via `$this->getDispatcher()->handle404()`.

**API handlers**:
- 3.4: extend `PKP\handler\APIHandler` (Slim v3); declare `$this->_endpoints = ['GET' => [['pattern' => 'submissions/{submissionId}', 'handler' => [$this, 'get'], 'roles' => [...]]]]`; method `(SlimRequest $slim, APIResponse $response, array $args)`; respond `$response->withJson($data, 200)`.
- 3.5: extend `PKP\core\PKPBaseController` (Laravel) — implement `getHandlerPath()`, `getRouteGroupMiddleware()`, `getGroupRoutes()` (Laravel `Route::get(...)` calls), return `JsonResponse`. Plugins register controllers via `APIHandler::endpoints::plugin` (settings) or modify per-entity via `APIHandler::endpoints::{entity}`.

**Controller (grid) handlers are deprecated** — build new UI with the UI Library + API handlers; existing grid plugins (staticPages) still work via `LoadComponentHandler`.

## 4. Authorization (REQUIRED for custom handlers)

Override `authorize()`, add policies, call parent:

```php
use PKP\security\authorization\ContextRequiredPolicy;
use PKP\security\authorization\RoleBasedHandlerOperationPolicy;
use PKP\security\Role;

public function __construct() {
    parent::__construct();
    $this->addRoleAssignment([Role::ROLE_ID_MANAGER], ['index', 'export']);
}

public function authorize($request, &$args, $roleAssignments) {
    $this->addPolicy(new ContextRequiredPolicy($request));
    foreach ($roleAssignments as $role => $operations) {
        $this->addPolicy(new RoleBasedHandlerOperationPolicy($request, $role, $operations));
    }
    return parent::authorize($request, $args, $roleAssignments);
}
```

Policy classes (`PKP\security\authorization`): `PKPSiteAccessPolicy` (logged-in site access), `ContextRequiredPolicy`, `RoleBasedHandlerOperationPolicy`, `WorkflowStageAccessPolicy` (use this for submission access, args `($request, $args, $roleAssignments, 'submissionId', $stageId)`), `PolicySet` (`COMBINING_PERMIT_OVERRIDES` / `COMBINING_DENY_OVERRIDES`), `AuthorizationPolicy`. Policies can stash objects: `addAuthorizedContextObject(Application::ASSOC_TYPE_SUBMISSION, $submission)` → in handler `getAuthorizedContextObject(Application::ASSOC_TYPE_SUBMISSION)`.

## 5. File storage (plugins should NOT use raw PHP file functions)

```php
$fileService = Services::get('file');                  // APP\core\Services
$fileId = $fileService->add($absoluteSourcePath, $destinationPath);  // also rows into `files` table
$file = $fileService->get($fileId);                    // ->path, ->mimetype
$fileService->download($file->path, 'report.pdf');
$fileService->delete($fileId);
$exists = $fileService->fs->has($path);                // Flysystem API underneath
```

Context dir: `Application::get()->getFileDirectories()['context'] . $context->getId()`; submission dir: `Repo::submissionFile()->getSubmissionDir($contextId, $submissionId)`. Public-files dir is legacy (`PublicFileManager`). UI uploads stage through the REST `temporaryFiles` endpoint.

## 6. Validation

Laravel validation everywhere (all rules except `exists`), plus custom rules: `email_or_localhost`, `issn`, `orcid`, `currency`.

```php
use PKP\validation\ValidatorFactory;
$validator = ValidatorFactory::make($props, ['contactEmail' => ['required', 'email_or_localhost']], $customMessages);
if ($validator->fails()) { $errors = $validator->errors(); }
```

Schema-level: each property's `"validation": [...]` array; **every optional property must include `"nullable"`**; `array/boolean/integer/string` derive from `type` automatically — don't repeat them.

## 7. Vue 3 backend extension (3.5)

- Runtime registry `pkp.registry` (from `js/classes/VueRegistry.js`): `registerComponent(name, component)` (global), `getComponent(name)` (to extend an existing one), `registerDirective`, `getPiniaStore(name)`, `storeExtend(store, fn)`, `storeExtendFn(store, fnName, fn)`, `storeAddFn`, `storeListExtendableFns`.
- Vue apps mount via `pkp.registry.init(elementId, componentType, initialConfig)`; pages pass initial state through `setState(['pageInitConfig' => …])`.
- JS hooks exist for injecting plugin components into: Dashboard, Workflow, FileManager, ReviewerManager, ParticipantManager, GalleyManager — see the 3.5 UI Library Storybook "Plugin Guide" and `github.com/jardakotesovec/backend-ui-example-plugin`.
- Smarty+Vue mixing is deprecated in the 3.5 backend; reader-facing frontend remains Smarty.

## 8. Useful data-access snippets (plugin/handler code)

```php
use APP\facades\Repo;

// Collector queries (3.4+)
$submissions = Repo::submission()->getCollector()
    ->filterByContextIds([$contextId])
    ->filterByStatus([\APP\submission\Submission::STATUS_PUBLISHED])
    ->limit(20)->getMany();

// Drop to the query builder for custom joins
$qb = Repo::submission()->getCollector()->filterByContextIds([$id])->getQueryBuilder();

// No Repo? Legacy DAO:
$reviewAssignmentDao = \PKP\db\DAORegistry::getDAO('ReviewAssignmentDAO');  // 3.4 only — removed in 3.5

// Current context (null on site-level pages)
$context = Application::get()->getRequest()->getContext();
```

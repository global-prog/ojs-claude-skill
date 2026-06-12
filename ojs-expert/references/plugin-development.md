# OJS Plugin Development (3.4.x / 3.5.x)

Verified against the PKP Plugin Guide (every chapter, version-tagged 3.5), `pkp/pluginTemplate` (`stable-3_4_0` = 3.4 pattern, `main` = 3.5 pattern), `pkp/pkp-lib` + `pkp/ojs` source, and real official plugins (staticPages, customBlockManager, webFeed, citationStyleLanguage, googleScholar, orcidProfile, crossref-ojs, pln, paypal). Hooks → `hooks-catalog.md`; Vue forms/fields, handlers, authorization → `ui-forms-handlers.md`.

## 1. Plugin anatomy

A minimal plugin needs exactly two files in `plugins/<category>/<name>/`:

```
plugins/generic/tutorialExample/
├── TutorialExamplePlugin.php    # main class (3.4+ uses .php; .inc.php NOT loaded in 3.5)
└── version.xml
```

Rules:
- Directory name: **letters and numbers only — no spaces, hyphens, or underscores** (camelCase).
- Class name = directory name, first letter capitalized, + `Plugin`: `tutorialExample` → `TutorialExamplePlugin`.
- Namespace (3.4+): `namespace APP\plugins\<category>\<name>;`
- 3.4 back-compat alias (omit in 3.5 — non-namespaced plugins are unsupported there):
  ```php
  if (!PKP_STRICT_MODE) {
      class_alias('\APP\plugins\generic\pluginTemplate\PluginTemplatePlugin', '\PluginTemplatePlugin');
  }
  ```

### version.xml (identical format 3.4/3.5)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE version SYSTEM "../../../lib/pkp/dtd/pluginVersion.dtd">
<version>
    <application>tutorialExample</application>   <!-- must match directory name -->
    <type>plugins.generic</type>                 <!-- plugins.<category> -->
    <release>1.0.0.0</release>                   <!-- ALWAYS four segments -->
    <date>2023-05-15</date>
    <lazy-load>1</lazy-load>                     <!-- for LazyLoadPlugin descendants -->
    <class>TutorialExamplePlugin</class>
</version>
```

### Minimal working generic plugin (verbatim from PKP docs)

```php
<?php
namespace APP\plugins\generic\tutorialExample;

use PKP\plugins\GenericPlugin;

class TutorialExamplePlugin extends GenericPlugin
{
    public function register($category, $path, $mainContextId = null)
    {
        $success = parent::register($category, $path);
        if ($success && $this->getEnabled()) {
            // Hook::add(...) calls go here — ALWAYS gate on getEnabled()
        }
        return $success;
    }

    public function getDisplayName()
    {
        return __('plugins.generic.tutorialExample.name');
    }

    public function getDescription()
    {
        return __('plugins.generic.tutorialExample.description');
    }
}
```

(3.5 template form: `parent::register($category, $path, $mainContextId)` and `$this->getEnabled($mainContextId)`.)

## 2. Plugin categories — verified base classes

Valid categories per `APP\core\Application::getPluginCategories()` (OJS 3.5, exact order — `metadata` loads first by design): `metadata`, `blocks`, `gateways`, `generic`, `importexport`, `oaiMetadataFormats`, `paymethod` (singular!), `pubIds`, `reports`, `themes`. **There is no `auth` category / `AuthPlugin` base class in 3.4/3.5.**

All base classes in `PKP\plugins`. Inheritance: `GenericPlugin` (empty marker), `ThemePlugin`, `BlockPlugin`, `PaymethodPlugin`, `PKPPubIdPlugin` extend `LazyLoadPlugin` → abstract `Plugin`. `ImportExportPlugin`, `ReportPlugin`, `GatewayPlugin`, `OAIMetadataFormatPlugin`, `MetadataPlugin` extend `Plugin` directly.

| Category | Base class | Must implement / key API |
|---|---|---|
| `generic` | `GenericPlugin` | `register()` + hooks |
| `themes` | `ThemePlugin` | `init()` — see theme-development.md |
| `blocks` | `BlockPlugin` | `getContents($templateMgr, $request = null)`; default template `block.tpl` via `getBlockTemplateFilename()`. Markup convention: `<div class="pkp_block"><h2 class="title">…</h2><div class="content">…</div></div>`. NOTE: no `BLOCK_CONTEXT_*` constants / `getSeq` / context-map methods exist in 3.4+. |
| `importexport` | `ImportExportPlugin` | abstract `executeCLI($scriptName, &$args)` + `usage($scriptName)`; `display($args, $request)` for web UI (call `parent::display()`, then branch on `array_shift($args)`); helpers: `getExportFileName()`, `setDeployment()`, `getImportedFilePath()`, `supportsCLI()` |
| `reports` | `ReportPlugin` | abstract `display($args, $request)` — stream CSV via headers + `fputcsv` |
| `gateways` | `GatewayPlugin` | abstract `fetch($args, $request)`. URL: `index.php/<context>/gateway/plugin/<pluginName>/<extraArgs...>` — GatewayHandler shifts the plugin name; the rest arrives as `$args`. Falsey return → redirect. Also `getPolicies($request)`. |
| `paymethod` | `PaymethodPlugin` | abstract `getPaymentForm($context, $queuedPayment)`, `saveSettings(string $hookName, array $args)`, `handle($args, $request)` (IPN/callbacks); `isConfigured($context)`. Real example: `plugins/paymethod/paypal` in pkp/ojs (Omnipay via composer). |
| `pubIds` | `PKPPubIdPlugin` (no `PubIdPlugin.php` exists; OJS app subclass `PubIdPlugin`) | ~18 abstracts incl. `getPubId($pubObject)`, `constructPubId($prefix, $suffix, int $contextId)`, `getPubIdType()` (e.g. `'other::urn'`), `getResolvingURL()`, `instantiateSettingsForm()`, `getFormFieldNames()`, `getDAOFieldNames()` (e.g. `['pub-id::other::urn']`). Canonical example: `plugins/pubIds/urn` in pkp/ojs. DOIs are NOT a pubId plugin since 3.4 (core DOI system). |
| `oaiMetadataFormats` | `OAIMetadataFormatPlugin` | abstract `getFormatClass()`; static `getMetadataPrefix()`, `getSchema()`, `getNamespace()`. Triad: plugin class + format class (extends `OAIMetadataFormat`, implements `toXml($record, $format = null)`) + `templates/record.tpl` crosswalk. Example: `plugins/oaiMetadataFormats/marc`. |
| `metadata` | `MetadataPlugin` | abstract `supportsFormat($format)`, `getSchemaObject($format)` |

## 3. `Plugin` root class — lifecycle API (verified 3.5)

| Method | Default / purpose |
|---|---|
| `register($category, $path, $mainContextId = null)` | wires install/template hooks; call parent |
| `getName()` | abstract on root; `LazyLoadPlugin` defaults to lowercased class name |
| `getDisplayName()` / `getDescription()` | abstract — required |
| `getSeq()` | `0` — registration order |
| `isSitePlugin()` | `false` — `true` puts plugin in site-wide plugins list |
| `getInstallMigration()` | `null` — return a Laravel `Migration` to create plugin tables (§4) |
| `getInstallEmailTemplatesFile()` | `null` — return path to an `emailTemplates.xml` (§4) |
| `getInstallSitePluginSettingsFile()` / `getContextSpecificPluginSettingsFile()` | `null` — settings.xml defaults |
| `getInstallFilterConfigFiles()` | filter configs (`filterConfig.xml`) |
| `getSetting($contextId, $name)` / `updateSetting($contextId, $name, $value, $type = null)` | settings storage (context-keyed; site = `Application::CONTEXT_SITE` = `0`). **CAUTION (observed on a live 3.5 install): `plugin_settings.context_id` carried a FK to `journals(journal_id)`, so an `updateSetting(0, …)` write at the SITE context fataled with an integrity-constraint violation (`SQLSTATE[23000] … plugin_settings_context_id`). If you need install-wide plugin state, store it PER-CONTEXT (under each journal) rather than at ctx 0, or verify your `plugin_settings` schema first. Reads at ctx 0 are safe (a `SELECT` doesn't hit the FK).** |
| `getActions($request, $actionArgs)` / `manage($args, $request)` | management UI entry points (§6) |
| `getTemplateResource($template = null, $inCore = false)` | Smarty resource for plugin templates |
| `getPluginPath()` / `getDirName()` / `getCategory()` / `getCurrentVersion()` | metadata |
| `getCanEnable()` / `getCanDisable()` / `getEnabled()` | `LazyLoadPlugin` makes these real (per-context enable state) |
| `addLocaleData()` / `smartyPluginUrl($params, $smarty)` | locale + `{plugin_url}` |

3.4→3.5 removals on this class: `import($class)` and `installEmailTemplateData()` gone; `getInstallEmailTemplateDataFile()` is now `final` and throws.

`PluginRegistry` (all static): `loadCategory($category, $enabledOnly = false)`, `loadPlugin($category, $name)`, `getPlugin($category, $name)`, `register($category, Plugin $plugin, $path)`, `getCategories()`, `loadAllPlugins()`. Loading a category is expensive — once per request.

## 4. Shipping DB tables, email templates, locales, composer deps

**Migration** (verified: pkp/staticPages):
```php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

class StaticPagesSchemaMigration extends Migration {
    public function up() {
        Schema::create('static_pages', function (Blueprint $table) {
            $table->bigInteger('static_page_id')->autoIncrement();
            $table->string('path', 255);
            $table->bigInteger('context_id');
        });
        Schema::create('static_page_settings', function (Blueprint $table) { /* … */ });
    }
    public function down(): void { Schema::drop('static_page_settings'); Schema::drop('static_pages'); }
}
// in the plugin class:
public function getInstallMigration() { return new StaticPagesSchemaMigration(); }
```

⚠️ **The install migration runs on BOTH fresh install and version upgrades** — `Plugin::register()` wires `updateSchema()` to the `Installer::postInstall` hook with no version gating, and there is **no `getUpgradeMigration()`**. Write migrations idempotently (`Schema::hasTable()` guards) or branch internally on the installed version. `php lib/pkp/tools/installPluginVersion.php <path>/version.xml` always runs the migration + settings/email/filter installs; `VersionDAO::insertVersion` handles the version bookkeeping (equal → update row, newer → new current row, downgrade → exception).

**Email templates** (verified: orcidProfile): `public function getInstallEmailTemplatesFile() { return $this->getPluginPath() . '/emailTemplates.xml'; }` — register the Mailable too via the `Mailer::Mailables` hook so it shows in the template UI.

**Locales**: `plugins/<cat>/<name>/locale/<locale>/locale.po` (short codes: `en`, `fr_CA` — never `en_US` in 3.4+). Keys `plugins.<category>.<name>.*`; use `__('key')` / `{translate key="…"}`. Auto-discovered (`Plugin::addLocaleData()` registers the dir via `Locale::registerPath`, called from `LazyLoadPlugin::register`). Never concatenate translated phrases. Two gotchas that cause `##key##` on a live site:
- **Blank line between every entry is mandatory** — the PO loader splits on blank lines; consecutive `msgid`/`msgstr` with no blank line between them drop all but the last of each block (a positional `##` pattern). `msgfmt -c` won't flag it but the loader does; match the bundled .po format.
- **Locale cache isn't rebuilt on plugin install** — newly added keys show `##` until **Administration → Clear Data Caches** (deletes `cache/fc-*`). Standard post-install step.

**Composer deps**: ship `composer.json` + `composer.lock` with `"config": {"vendor-dir": "lib/vendor"}` (isolates from core vendor tree); deps installed at build/release (verified: citationStyleLanguage, paypal).

## 5. Hooks (summary — full catalog in `hooks-catalog.md`)

```php
use PKP\plugins\Hook;
Hook::add('Name', [$this, 'callback']);          // or first-class callable: $this->callback(...)
// callback: function(string $hookName, array $args): bool
// return Hook::CONTINUE (false) or Hook::ABORT (true)
```

The workhorse hooks: `LoadHandler` (custom pages), `LoadComponentHandler` (grids), `TemplateResource::getFilename` (template overrides via `_overridePluginTemplates`), `Templates::*` (output injection), `Schema::get::<entity>` + `Form::config::before` (custom fields), entity lifecycle (`Publication::publish`, `Submission::add`…), `ArticleHandler::view/download` (article page/galley takeover), `APIHandler::endpoints::{entity}` (3.5 API extension), `Mailer::Mailables`. ALWAYS check `$this->getEnabled()` before adding hooks; hooks are reliable only from **generic** plugins.

## 6. Plugin settings UI — 3.4 vs 3.5

Storage is identical (`getSetting`/`updateSetting`). The UI differs:

### 3.4: `getActions()` + `manage()` + Smarty `Form` in `AjaxModal`
```php
public function getActions($request, $actionArgs)
{
    $actions = parent::getActions($request, $actionArgs);
    if (!$this->getEnabled()) return $actions;
    $router = $request->getRouter();
    array_unshift($actions, new LinkAction(
        'settings',
        new AjaxModal(
            $router->url($request, null, null, 'manage', null,
                ['verb' => 'settings', 'plugin' => $this->getName(), 'category' => 'generic']),
            $this->getDisplayName()
        ),
        __('manager.plugins.settings'), null
    ));
    return $actions;
}

public function manage($args, $request)
{
    switch ($request->getUserVar('verb')) {
        case 'settings':
            $form = new MySettingsForm($this);          // extends PKP\form\Form, renders settings.tpl
            if (!$request->getUserVar('save')) {
                $form->initData();
                return new JSONMessage(true, $form->fetch($request));
            }
            $form->readInputData();
            if ($form->validate()) { $form->execute(); return new JSONMessage(true); }
    }
    return parent::manage($args, $request);
}
```

### 3.5: `PluginSettingsController` + `FormComponent` + Vue `PkpFormModal`
The 3.5 guide documents ONLY this pattern (legacy verbs undocumented). Three pieces — full working example in `pkp/pluginTemplate` branch `main`:
```php
// (a) action opens a Vue modal pointed at the plugin's settings API
$apiUrl = $request->getDispatcher()->url($request, Application::ROUTE_API,
    $context->getPath(), $this->controller->getHandlerPath());   // "plugins/<name>/settings"
$form = new MySettingsForm($apiUrl);
array_unshift($actions, new LinkAction('settings',
    new VueModal('PkpFormModal', [
        'title' => $this->getDisplayName(),
        'formConfig' => $form->getConfig(),
        'getApiUrl' => $apiUrl,
    ]), __('manager.plugins.settings'), null));

// (b) form = FormComponent with Field* objects (see ui-forms-handlers.md for the field inventory)
class MySettingsForm extends \PKP\components\forms\FormComponent {
    public $id = 'mySettings';
    public $method = 'PUT';
    public function __construct(string $action) {
        $this->action = $action;
        $this->addField(new \PKP\components\forms\FieldText('myField', [
            'label' => __('plugins.generic.myPlugin.myField'), 'value' => '',
        ]));
    }
}

// (c) controller extends PKP\plugins\PluginSettingsController; register via:
Hook::add('APIHandler::endpoints::plugin', function (string $hookName, $apiRouter): bool {
    $apiRouter->registerPluginApiControllers([$this->controller]);
    return Hook::CONTINUE;
});
// Routes auto-mapped: GET '' -> get(Request): JsonResponse, PUT '' -> edit(FormRequest): JsonResponse
// Middleware: has.user; site plugins need ROLE_ID_SITE_ADMIN, context plugins ROLE_ID_MANAGER.
```

## 7. Templates, assets, custom pages

```php
use APP\template\TemplateManager;
$templateMgr = TemplateManager::getManager($request);
$templateMgr->display($this->getTemplateResource('example.tpl'));

// Override core/other-plugin templates (register once):
Hook::add('TemplateResource::getFilename', [$this, '_overridePluginTemplates']);
// plugin's templates/common/footer.tpl now overrides the app's; mirror full path for
// other plugins: templates/plugins/blocks/<name>/templates/block.tpl

// CSS/JS (default context: frontend)
$url = $request->getBaseUrl() . '/' . $this->getPluginPath() . '/css/my.css';
$templateMgr->addStyleSheet('myStyles', $url, ['contexts' => 'backend']);
$templateMgr->addJavaScript('myScript', $jsUrl, ['contexts' => ['frontend', 'backend']]);
// <meta>/<link> tags (e.g. Google Scholar citation_* tags):
$templateMgr->addHeader('myMeta', '<meta name="citation_title" content="…"/>');
```

**Custom page** (canonical pattern, verified in staticPages):
```php
Hook::add('LoadHandler', [$this, 'setPageHandler']);
public function setPageHandler($hookName, $args) {
    $page =& $args[0]; $op =& $args[1]; $handler =& $args[3];
    if ($this->getEnabled() && $page === 'example') {
        $handler = new ExampleHandler($this);   // extends PKP\controllers\page\PageHandler or APP\handler\Handler
        return true;                            // ABORT — handler claimed
    }
    return false;
}
```
One public method per op (`index($args, $request)` for op-less URLs); render via `getTemplateResource()`. **Add authorization** — override `authorize()` with policies (see ui-forms-handlers.md §4). In 3.5 `HANDLER_CLASS` is removed — the by-reference `$args[3]` form is required.

## 8. Background work from plugins

**Queue jobs** (3.4+): class extends `PKP\jobs\BaseJob` (namespace root `jobs/` dir of pkp-lib; `$tries=3`, db connection/queue from config), constructor calls `parent::__construct()`, implement `handle(): void` (+ optional `failed()`); dispatch with `dispatch(new MyJob($args))`. Use ONLY the default queue/database driver — never `onQueue()`/`onConnection()`. Verified core examples: `PKP\jobs\orcid\DepositOrcidSubmission`, `PKP\jobs\doi\DepositSubmission`.

**Scheduled tasks — 3.5** (Acron + `scheduledTasks.xml` + `AcronPlugin::parseCronTab` hook are GONE):
```php
use PKP\plugins\interfaces\HasTaskScheduler;
use PKP\scheduledTask\PKPScheduler;

class MyPlugin extends GenericPlugin implements HasTaskScheduler {
    public function registerSchedules(PKPScheduler $scheduler): void {
        $scheduler->addSchedule(new MyTask([]))      // MyTask extends PKP\scheduledTask\ScheduledTask
            ->hourly()                               // Laravel frequencies: daily(), everyMinute(), …
            ->name(MyTask::class)
            ->withoutOverlapping();
    }
}
// Task class: extend ScheduledTask, implement protected function executeActions(): bool
```
(Verified in pkp/crossref-ojs and pkp/pln `main` branches.) **3.4**: ship `scheduledTasks.xml` (`<task class="…"><frequency hour="24"/></task>`) consumed by the Acron plugin.

**Laravel events (3.4+)** — alternative to hooks for core events like `DecisionAdded`:
```php
use Illuminate\Support\Facades\Event;
Event::subscribe(new MyListener());   // in register()
class MyListener {
    public function subscribe($events): void {
        $events->listen(\PKP\observers\events\DecisionAdded::class, self::class);
    }
    public function handle(\PKP\observers\events\DecisionAdded $event) { /* $event->submission … */ }
}
```
Events live in `lib/pkp/classes/observers/events/` + `classes/observers/events/`.

## 9. Notifications from plugins

3.5 rewrote notifications on Eloquent: `PKP\notification\Notification extends Model` (table `notifications`); constants moved from the removed `PKPNotification` onto it; `NotificationDAO` removed.

```php
use PKP\notification\Notification;
use APP\notification\NotificationManager;

$notificationManager = new NotificationManager();
// 3.5 signature (⚠️ BREAKING: 3.4 took $request as FIRST argument — drop it when migrating):
$notificationManager->createNotification(
    $userId,                                       // ?int
    Notification::NOTIFICATION_TYPE_SUCCESS,       // ?int type
    $contextId,                                    // default Application::SITE_CONTEXT_ID
    $assocType, $assocId,                          // optional association
    Notification::NOTIFICATION_LEVEL_NORMAL,       // TRIVIAL=1, NORMAL=2, TASK=3
    ['contents' => __('plugins.generic.myPlugin.notify')]   // params
);
// Quick toast: createTrivialNotification($userId, Notification::NOTIFICATION_TYPE_SUCCESS, $params)
```

Custom types: offset from `Notification::NOTIFICATION_TYPE_PLUGIN_BASE` (`0x6000001`). Presentation (message/URL/icon) dispatches through `PKPNotificationManager::getNotificationMessage()` and per-type `NotificationManagerDelegate` subclasses (constructor takes the type int; override `getNotificationMessage/Url/Contents`, `getStyleClass`, `isVisibleToAllUsers`). Example delegate + batch pattern: `jobs/notifications/NewAnnouncementNotifyUsers` + `managerDelegate/AnnouncementNotificationManager`.

## 10. Custom Mailables from a plugin

```php
use PKP\mail\Mailable;
use PKP\mail\traits\{Recipient, Sender, Configurable, Unsubscribe};

class MyPluginNotify extends Mailable
{
    use Recipient;      // ->recipients([$user], $locale)  (to() throws — forces this)
    use Configurable;   // makes it editable in Workflow → Emails UI
    // use Sender;      // ->sender($user)  (from() throws)
    // use Unsubscribe; // ->allowUnsubscribe($notification) + List-Unsubscribe header

    protected static ?string $name = 'plugins.generic.myPlugin.mailable.name';
    protected static ?string $description = 'plugins.generic.myPlugin.mailable.description';
    protected static ?string $emailTemplateKey = 'MY_PLUGIN_NOTIFY';
    protected static array $groupIds = [self::GROUP_OTHER];   // or GROUP_SUBMISSION/REVIEW/COPYEDITING/PRODUCTION
    protected static bool $canDisable = true;

    public function __construct(Context $context /* , ...data */) { parent::__construct([$context]); }
}

// Send (3.5): Laravel facade
use Illuminate\Support\Facades\Mail;
Mail::send((new MyPluginNotify($context))->recipients([$user])->setLocale($locale));
```

Register so it appears in the email-templates UI: `Mailer::Mailables` hook (push the class name into the Collection). Ship the default template via `getInstallEmailTemplatesFile()` pointing at:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE emails SYSTEM "../../../lib/pkp/dtd/emailTemplates.dtd">
<emails>
    <email key="MY_PLUGIN_NOTIFY"
           name="plugins.generic.myPlugin.emails.notify.name"
           subject="emails.myPluginNotify.subject"
           body="emails.myPluginNotify.body"/>   <!-- attrs are LOCALE KEYS; alternateTo optional -->
</emails>
```

## 11. Full custom REST API endpoints from a plugin

**3.5 (Laravel):** controller extends `PKP\core\PKPBaseController` with three required methods, registered via the `APIHandler::endpoints::plugin` hook (the APIRouter is passed; `getHandlerPath()` is a free-form path — `/api/v1/<handlerPath>/...`):

```php
use PKP\core\PKPBaseController;
use Illuminate\Support\Facades\Route;
use PKP\security\Role;

class MyController extends PKPBaseController
{
    public function getHandlerPath(): string { return 'myplugin'; }
    public function getRouteGroupMiddleware(): array
    {
        return ['has.user', 'has.context',
            self::roleAuthorizer([Role::ROLE_ID_MANAGER, Role::ROLE_ID_SITE_ADMIN])];
    }
    public function getGroupRoutes(): void
    {
        Route::get('items', $this->getItems(...))->name('myplugin.getItems');
        Route::post('items', $this->addItem(...))->name('myplugin.addItem');
    }
    public function getItems(Request $illuminateRequest): JsonResponse { /* ... */ }
}

// in register():
Hook::add('APIHandler::endpoints::plugin', function (string $hookName, $apiRouter): bool {
    $apiRouter->registerPluginApiControllers([new MyController()]);   // throws on duplicate handler path
    return Hook::CONTINUE;
});
```

Modify EXISTING endpoints via the per-entity hook `APIHandler::endpoints::{entity}` (e.g. `::submissions`) — args `[$controller, $apiHandler]`.

**3.4 (Slim):** handler extends `PKP\handler\APIHandler`; declare in the constructor:
```php
$this->_endpoints = ['GET' => [[
    'pattern' => $this->getEndpointPattern() . '/items',
    'handler' => [$this, 'getItems'],     // (SlimRequest $req, APIResponse $res, array $args)
    'roles'   => [Role::ROLE_ID_MANAGER],
]]];
```

## 12. Import/export filters (Native XML framework)

Filters transform objects ↔ XML; registered via `filterConfig.xml` (returned from `getInstallFilterConfigFiles()`):

```xml
<filterConfig>
  <filterGroup symbolic="article=>native-xml"
      displayName="plugins.importexport.myPlugin.displayName"
      description="..."
      inputType="class::classes.submission.Submission[]"
      outputType="xml::schema(plugins/importexport/myPlugin/my.xsd)" />
  <filter inGroup="article=>native-xml"
      class="APP\plugins\importexport\myPlugin\filter\ArticleMyXmlFilter"
      isTemplate="0" />
</filterConfig>
```

Class chains (core native plugin, the canonical reference): export `ArticleNativeXmlFilter → SubmissionNativeXmlFilter → NativeExportFilter → PKPImportExportFilter → PersistableFilter`; import mirrors with `NativeXml*Filter → NativeImportFilter`. Note: `pkp/exampleImportExport` exists but has **no 3.4/3.5 branch** (3.3-era) — use it for scaffolding shape only; copy filter patterns from `plugins/importexport/native` in the live install.

## 13. Advanced extension points

- **Custom editorial decision**: hook `Decision::types` (`$args[0]` = Eloquent Collection of `DecisionType`s — filter/map/push) and `Workflow::Decisions` (`$args[0]` array, `$args[1]` `$stageId`). New types extend `PKP\decision\DecisionType`, use constants in the **900 range**, implement `getDecision()`, `getStageId()`, `getSteps()`, `validate()`, `runAdditionalActions()`.
- **Extend REST API output (maps)**: `app('maps')->extend(\PKP\announcement\maps\Schema::class, fn($output, $item, $map) => $output + ['myProp' => …]);`
- **Custom fields**: `Schema::get::<entity>` (add `(object)['type'=>'string','multilingual'=>true,'apiSummary'=>true,'validation'=>['nullable']]` to `$schema->properties`) + `Form::config::before` (guard on `$form->id`, then `$form->addField(...)`). Read with `$entity->getLocalizedData('field')`. Persisted automatically; surfaces in the API.
- **Dynamic plugin instances** (verified: customBlockManager): a parent plugin registers N runtime instances: `PluginRegistry::register('blocks', new CustomBlockPlugin($name, $this), $this->getPluginPath());` with `getName()` returning the dynamic name.
- **Multi-plugin bundles** (verified: webFeed): one generic plugin registers companion block + gateway plugins from `register()`.
- **External APIs/OAuth** (verified: orcidProfile 3.4): custom page handler ops for the OAuth redirect/callback; HTTP via the shared Guzzle client `Application::get()->getHttpClient()`; tokens persisted with `updateSetting()`.
- **Backend UI in Vue (3.5)**: recommended over Smarty pages. JS extension API at `pkp.registry` (from `js/classes/VueRegistry.js`): `registerComponent(name, comp)`, `getComponent(name)` (extend existing fields), `storeExtend/storeExtendFn/storeAddFn` (pinia stores). JS hooks exist to inject components into Dashboard, Workflow, FileManager, ReviewerManager, ParticipantManager, GalleyManager. Load the built bundle via `addJavaScript(..., ['contexts' => 'backend'])`. Examples: Storybook "Plugin Guide" section of the 3.5 UI library; `github.com/jardakotesovec/backend-ui-example-plugin`. Smarty for plugin backend pages (LoadHandler handlers, settings-tab injection like staticPages' `Template::Settings::website` hook) still works in 3.5 — deprecated, not removed.
- **Role/permission checks** (3.5): `$user->hasRole([Role::ROLE_ID_MANAGER], $contextId)` (int or array); `Repo::userGroup()->userInGroup($userId, $userGroupId)`, `->userUserGroups($userId, $contextId)`, `->getByRoleIds([Role::ROLE_ID_REVIEWER], $contextId)`. `UserGroup` is Eloquent in 3.5 with scopes (`withContextIds`, `withRoleIds`, `withStageIds`, `masthead`…).
- **Custom navigation menu item types**: `NavigationMenus::itemTypes` / `::itemCustomTemplates` / `::displaySettings` hooks — array shapes in `frontend-templating.md` §5.
- **Custom Smarty tags**: `$templateMgr->registerPlugin('function', 'my_tag', [$this, 'smartyMyTag'])` — standard Smarty API on PKPTemplateManager.
- **TinyMCE**: the tinymce plugin exposes **no extension hook** for editor config — there is no supported way for another plugin to alter TinyMCE init options.

## 14. Testing, CI, distribution

- **CI** (verified: staticPages/customBlockManager): `.github/workflows/<branch>.yml` using the composite action `pkp/pkp-github-actions@v1` with `plugin: true`, a matrix over `{application: ojs, php-version, database: mysql|pgsql}`; tests are **Cypress** functional specs in `cypress/tests/functional/`.
- **Package**: `.tar.gz` with one top-level dir matching the product name; GPL-compatible `LICENSE`; exclude composer/npm dev cruft. `npm i -g pkp-plugin-cli && pkp-plugin release <name> --newversion 1.0.0.0`.
- **Gallery**: PR to `github.com/pkp/plugin-gallery` — `<plugin category product>` XML with `<release date version md5>`, `<compatibility><version>` tags, `<certification type="official|reviewed|partner"/>`. Releases are immutable once merged.
- **Manual install**: extract into `plugins/<category>/`, run `php lib/pkp/tools/installPluginVersion.php plugins/<category>/<name>/version.xml`, clear caches.
- **Programmatic in-request upgrade** (verified `PKP\plugins\PluginHelper`, stable-3_5_0): `(new PluginHelper())->upgradePlugin(string $category, string $plugin, string $path, string $originalFileName): Version`. `$plugin` must equal version.xml `<product>`/`<application>`; `$path` is the `.tar.gz` on disk; `$originalFileName` MUST carry the archive extension (`.tar.gz`) — PharData keys off it. It REFUSES non-newer versions (`manager.plugins.installedVersionNewer`), validates the package's product/type, `rmtree`+`copyDir`s into `plugins/<category>/<plugin>`, `insertVersion()`s, runs `upgrade.xml` if present, and surfaces a non-writable plugins dir as a localized `Exception` (`manager.plugins.deleteError`). It does **no** checksum (verify your own) and cleans its **own** extraction temp dir (you only delete the `.tar.gz` you downloaded). Reference caller: `PluginGalleryGridHandler::installPlugin` (downloads → md5-checks → upgrades). Self-upgrade caveat: it `rmtree`s the plugin's own dir, so trigger it from a dedicated request (a handler op), not mid-render; and clear `cache/t_compile`+`t_cache`+`_db` afterward yourself.

## 15. 3.4 → 3.5 migration checklist for plugins

1. PHP 8.2+; delete the `PKP_STRICT_MODE`/`class_alias` block; `.php` + namespace mandatory.
2. Replace removed hooks (full list in hooks-catalog.md §10) — registering them triggers deprecation warnings via `Hook::addUnsupportedHooks()`.
3. `HANDLER_CLASS` removed → `LoadHandler` 4th-param by-reference form.
4. Settings UI → `PluginSettingsController` + `FormComponent` + `VueModal` (§6).
5. API code: Slim → Laravel; `APIHandler::endpoints` → `APIHandler::endpoints::{entity}` / `::plugin`.
6. Scheduled tasks: `scheduledTasks.xml`/Acron → `HasTaskScheduler::registerSchedules()` (§8).
7. Email: `Mail::send` hook gone → `Email::send::before` hook, `Mailer::Mailables`, Laravel mail events.
8. Vue 2 → Vue 3: Options API/mixins deprecated → Composition API/composables; `ListPanel` → `Table`; use `pkp.registry` for component/store extension; don't pass translations via props.
9. `fatalError()` → exceptions; Stringy → `Illuminate\Support\Str`; `*_codesafe` functions removed.
10. Vendor JS paths moved (jQuery, jQuery UI, jQuery Validation, ChartJS) — fix hardcoded asset URLs.
11. More DAOs replaced by `Repo::`/Eloquent (e.g. `ReviewAssignmentDAO`, `NotificationDAO` removed) — test all data access.
12. `createNotification()` signature changed: drop the leading `$request` argument; constants moved `PKPNotification` → `PKP\notification\Notification` (§9).

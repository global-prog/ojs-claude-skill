# OJS Theme Development (3.4.x / 3.5.x)

Verified against the PKP Theming Guide (`docs.pkp.sfu.ca/pkp-theming-guide/en/` — note: only this legacy URL exists; there is no `/dev/theming-guide/`), `pkp-lib` `classes/plugins/ThemePlugin.php` (identical API in 3.4 and 3.5), and the OJS default theme source.

**Caveat:** the theming guide's `theme-setup` page still shows pre-3.4 syntax (`.inc.php`, `import()`, dated 2016). Do NOT reproduce it. Use the namespaced form below.

## 1. Theme plugin skeleton

```
plugins/themes/myTheme/
├── MyThemePlugin.php
├── version.xml                  # <type>plugins.themes</type>, <lazy-load>1</lazy-load>
├── styles/index.less
├── js/main.js
└── templates/…                  # template overrides (mirrors core paths)
```

```php
<?php
namespace APP\plugins\themes\myTheme;

use PKP\plugins\ThemePlugin;

class MyThemePlugin extends ThemePlugin
{
    public function init()
    {
        // ALL theme configuration happens here. init() runs only for the
        // active theme (and its parents).
        $this->addStyle('stylesheet', 'styles/index.less');
        $this->addScript('main', 'js/main.js');
        $this->addMenuArea(['primary', 'user']);
    }

    public function getDisplayName()
    {
        return __('plugins.themes.myTheme.name');
    }

    public function getDescription()
    {
        return __('plugins.themes.myTheme.description');
    }
}
```

## 2. ThemePlugin API (verified signatures — identical 3.4/3.5)

```php
abstract public function init();
public function addStyle($name, $style, $args = [])
public function addScript($name, $script, $args = [])
public function addOption($name, $type, $args = [])
public function addMenuArea($menuAreas)                 // string or array
public function modifyStyle($name, $args = [])
public function removeStyle($name)
public function modifyScript($name, $args = [])
public function removeScript($name)
public function setParent($parent)                      // parent plugin name lowercased
public function getOption($name)
public function getOptionValues(?int $contextId)
public function getOptionsConfig()
```

### addStyle args
- `context`: `'frontend'` (default) or `'backend'`
- `priority`: print order
- `addLess`: **array** of extra LESS files compiled before the main file
- `addLessVariables`: string of LESS variable overrides, e.g. `"@bg:#000;"`
- `inline`: bool — `$style` is raw CSS data

`.less` files are auto-compiled to CSS. `addLessVariables`/`addLess` are the mechanism for colour/typography options.

### addScript args
- `context`: `'frontend'` (default) or `'backend'`
- `priority`
- `inline`: bool — `$script` is raw JS (commonly used to pass data to the frontend)

### addOption — theme options shown in Website Settings → Appearance
`$type` = a UI field class name: any `PKP\components\forms\Field*` **except** `FieldUpload`/`FieldUploadImage`. Common: `FieldColor`, `FieldOptions` (radio/checkbox), `FieldText`.

```php
$this->addOption('baseColour', 'FieldColor', [
    'label' => __('plugins.themes.myTheme.option.colour.label'),
    'description' => __('plugins.themes.myTheme.option.colour.description'),
    'default' => '#1E6292',
]);
// later, e.g. in init():
if ($this->getOption('baseColour') !== '#1E6292') {
    $this->modifyStyle('stylesheet', [
        'addLessVariables' => '@primary:' . $this->getOption('baseColour') . ';',
    ]);
}
```

## 3. Child themes

```php
public function init()
{
    $this->setParent('defaultthemeplugin');   // = parent class name, lowercased

    // EITHER: own standalone stylesheet
    $this->addStyle('child-stylesheet', 'styles/index.less');

    // OR: merge into the parent's compiled LESS (preferred for variable overrides)
    $this->modifyStyle('stylesheet', ['addLess' => ['styles/index.less']]);
}
```

- Parent's `init()` runs first automatically; child can then modify/remove parent assets.
- Override parent LESS variables in the child LESS file: `@primary: #b21a00;`
- Multi-level inheritance works.

## 4. Template hierarchy & overrides

Smarty template lookup order (first match wins):
1. active (child) theme `templates/`
2. parent theme `templates/` (if any)
3. application `templates/` (OJS root)
4. `lib/pkp/templates/`

To override a template, mirror its path inside the theme, e.g. `plugins/themes/myTheme/templates/frontend/pages/article.tpl`.

### Frontend template structure
- `templates/frontend/pages/` — one template per public page
- `templates/frontend/objects/` — entity renderings used by pages
- `templates/frontend/components/` — small reusable pieces

OJS 3.5 `templates/frontend/pages/` (verified inventory): `aboutThisPublishingSystem.tpl`, `article.tpl`, `catalogCategory.tpl`, `indexJournal.tpl`, `indexSite.tpl`, `issue.tpl`, `issueArchive.tpl`, `purchaseIndividualSubscription.tpl`, `purchaseInstitutionalSubscription.tpl`, `search.tpl`, `submissions.tpl`, `subscriptions.tpl`, `userSubscriptions.tpl`.

`objects/`: `article_details.tpl`, `article_summary.tpl`, `galley_link.tpl`, `issue_summary.tpl`, `issue_toc.tpl` (+ possibly more). `components/`: `breadcrumbs_article.tpl`, `breadcrumbs_issue.tpl`, `notification.tpl`, `primaryNavMenu.tpl`, `skipLinks.tpl`, `subscriptionContact.tpl`.

Shared templates (header, footer, announcement objects, author pages, form components) live in `lib/pkp/templates/frontend/` — check the live install for the authoritative list.

**After editing templates, always clear the compiled-template cache** (`cache/t_compile/`).

## 5. Real-world example: the default theme

`plugins/themes/default/DefaultThemePlugin.php` (OJS) demonstrates: typography option as `FieldOptions` radio with 7 font stacks, `FieldColor` base colour (default `#1E6292`), conditional `addStyle` of font CSS, jQuery/Bootstrap/Swiper via `addScript`, `addMenuArea(['primary', 'user'])`, and option-driven `addLessVariables`. Read it in the live install as the canonical pattern.

## 6. Backend theming & 3.5 notes

- Inject backend CSS with `addStyle('name', 'styles/backend.css', ['context' => 'backend'])`.
- 3.5: the editorial UI moved further to Vue 3 + Tailwind; Smarty backend pages are deprecated. Frontend (reader-facing) theming remains Smarty + LESS exactly as in 3.4 — the ThemePlugin API did not change between 3.4 and 3.5.
- 3.4 locale change affects themes too: `locale/en_US/` → `locale/en/`, `.po` files.

## 7. Theme debugging checklist

1. Theme not listed? — `version.xml` `<type>plugins.themes</type>` + `<lazy-load>1</lazy-load>` + class/dir naming match; check PHP error log for namespace/class-name mismatch.
2. Styles not updating? — LESS is compiled and cached: clear `cache/` (template + data caches), hard-reload browser.
3. Template edit not appearing? — wrong lookup path (mirror the exact core path) or stale `cache/t_compile/`.
4. Option not applying? — options are saved per-context in Website Settings → Appearance; `getOption()` returns the saved value, defaults only after save.

# OJS Theme Development (3.4.x / 3.5.x)

Verified against the PKP Theming Guide, `ThemePlugin.php` (identical API 3.4/3.5), the OJS 3.5 default theme, and official theme repos (defaultManuscript, immersion, bootstrap3, healthSciences, classic, pragma). Smarty tags, template variables, menus/sidebar machinery → `frontend-templating.md`.

## 1. Theme plugin skeleton

```
plugins/themes/myTheme/
├── MyThemePlugin.php            # namespaced .php (3.4+)
├── version.xml                  # <type>plugins.themes</type>, <lazy-load>1</lazy-load>
├── styles/index.less            # entry point (+ variables.less, rtl.less…)
├── js/main.js
├── locale/en/locale.po
└── templates/…                  # overrides, mirroring core paths
```

```php
<?php
namespace APP\plugins\themes\myTheme;

use PKP\plugins\ThemePlugin;

class MyThemePlugin extends ThemePlugin
{
    public function init()
    {
        // ALL configuration here; runs only for the active theme (+ parents)
        $this->addStyle('stylesheet', 'styles/index.less');
        $this->addScript('main', 'js/main.js');
        $this->addMenuArea(['primary', 'user']);
    }

    public function getDisplayName() { return __('plugins.themes.myTheme.name'); }
    public function getDescription() { return __('plugins.themes.myTheme.description'); }
}
```

⚠️ The standalone official theme repos (classic, immersion, healthSciences, pragma) still ship legacy `.inc.php` + `HookRegistry::add` even on their `stable-3_5_0` branches — do **not** copy that style for new themes; only their *patterns* (below). `pkp/academicFree` does not exist.

## 2. ThemePlugin API (verified, identical 3.4/3.5)

```php
abstract public function init();
public function addStyle($name, $style, $args = [])     // args: context ('frontend'|'backend'|custom),
                                                        //       priority, addLess[], addLessVariables, inline
public function addScript($name, $script, $args = [])  // args: context, priority, inline
public function addOption($name, $type, $args = [])    // type: any Field* except FieldUpload/FieldUploadImage
public function addMenuArea($menuAreas)                 // string|array
public function modifyStyle($name, $args = [])         // merge args into an existing (incl. parent) style
public function removeStyle($name) / removeScript($name) / modifyScript($name, $args = [])
public function setParent($parent)                      // parent plugin name, lowercased
public function getOption($name) / getOptionsConfig() / getOptionValues(?int $contextId)
public function removeOption($name) / modifyOptionsConfig()
```

`.less` files auto-compile server-side (cached — clear `cache/` after changes). `addLess` (array of extra LESS files) and `addLessVariables` (string of `@var: value;` overrides) are the customization mechanism. `$min = Config::getVar('general', 'enable_minified') ? '.min' : ''` is the standard toggle for shipping minified assets.

## 3. Default theme LESS variables (verified `styles/variables.less`, OJS 3.5)

| Variable | Default | Notes |
|---|---|---|
| `@bg-base` | `#1E6292` | **header/accent background — this is what the "Base Colour" theme option writes** |
| `@primary` | `#006798` | links/buttons — a SEPARATE variable (common trap!) |
| `@primary-lift` | `lighten(@primary, 10%)` | hover states |
| `@bg` / `@bg-shade` | `#fff` / `#ddd` | page background / shaded areas |
| `@text` / `@text-light` | `rgba(0,0,0,0.87)` / `rgba(0,0,0,0.54)` | |
| `@text-bg-base` | `#fff` | text on `@bg-base` (default theme auto-darkens it for light base colours via `isColourDark()`) |
| `@font` | Noto Sans stack | `@font-heading`, `@font-site-title` default to it |
| `@rem` | `14px` | root size; spacing scale `@base 0.714rem`, `@double 1.43rem`, `@triple`, `@quadruple` |
| `@screen-phone/tablet/desktop/lg-desktop` | 480/768/992/1200px | each has a `-container` variant (−40px) |
| `@sidebar-width` | `300px` · `@radius` `3px` · `@normal/@bold` `400/700` | |

Default theme `styles/`: `index.less` (entry; imports pkp-lib shared `fontawesome/normalize/variables/utils/helpers/orcid.less` first, then theme files, **`rtl.less` last**), `variables.less`, `body/head/main/components/footer/sidebar.less`, `components/`, `fonts/`, `objects/`, `pages/`.

## 4. Child themes — canonical pattern (verified: pkp/defaultManuscript)

```php
public function init()
{
    $this->setParent('defaultthemeplugin');

    // Append child LESS into the parent's already-registered stylesheet:
    $this->modifyStyle('stylesheet', ['addLess' => ['styles/index.less']]);

    // Curate inherited options:
    $this->removeOption('typography');
    $this->removeOption('useHomepageImageAsHeader');
    $this->addOption('accentColour', 'FieldColor', [
        'label' => __('plugins.themes.defaultManuscript.option.accentColour.label'),
        'default' => '#F7BC4A',
    ]);

    // Inject computed variable overrides:
    $additionalLessVariables = [];
    if ($this->getOption('baseColour') !== '#1E6292') {
        $additionalLessVariables[] = '@bg-base:' . $this->getOption('baseColour') . ';';
    }
    $this->modifyStyle('stylesheet', ['addLessVariables' => join('', $additionalLessVariables)]);
}
```

- Parent's `init()` runs first; child then modifies/removes parent assets and options. Multi-level inheritance works.
- Override variables in child LESS too: `@primary: #4b7d92; @font-heading: "Montserrat", sans-serif;`.
- defaultManuscript ships **no templates/ dir** (pure restyle) and **its own `rtl.less`** — both legitimate choices.

## 5. Template hierarchy & overrides

Lookup order (first wins): **child theme → parent theme → app `templates/` → `lib/pkp/templates/`**. Override by mirroring the exact path, e.g. `plugins/themes/myTheme/templates/frontend/objects/article_details.tpl`. Full inventory of what exists to override → `frontend-templating.md` §3. **Clear `cache/t_compile/` after template edits.**

Immersion (most heavily templated official theme) overrides ~27 page templates + all 6 OJS objects — read it for full-redesign patterns.

## 6. Patterns from official themes (all verified in source)

- **Custom data for templates** (healthSciences, immersion): hook `TemplateManager::display`, guard on template name, `$templateMgr->assign(...)`. Only top-level `frontend/pages/*` templates fire it usefully.
- **Themes are full plugins — they may register hooks and extend entities** (immersion): `Schema::get::issue` to add a per-issue colour property + `issueform::display/initdata/readuservars/execute` form hooks + `Templates::Editor::Issues::IssueData::AdditionalMetadata` backend injection. Use sparingly; it couples the theme to data.
- **Build pipelines** (immersion, healthSciences): Gulp 4 + Dart Sass + Bootstrap 5 → committed `resources/dist/app.min.css|js`, loaded via plain `addStyle`/`addScript`. LESS-free themes are fine — `addStyle` with `.css` works.
- **Style variants as an option** (bootstrap3): a `FieldOptions` radio chooses among 18 pre-compiled Bootswatch LESS entries; `init()` conditionally `addStyle`s the chosen one.
- **Scoped asset contexts** (immersion): `addStyle('htmlGalley', '...', ['contexts' => 'htmlGalley'])` styles the HTML-galley viewer; `['contexts' => 'backend-manageIssues']` loads an asset only on a specific backend page.
- **Homepage image as header** (default theme): `addStyle('homepageImage', '.pkp_structure_head { background: ... }', ['inline' => true])`.

## 7. RTL support (Arabic, Hebrew, Farsi…)

OJS sets `dir="rtl"` on `<body>` automatically for RTL locales (`$currentLocaleLangDir`). Three verified mechanisms:

1. **Default theme:** ship `styles/rtl.less`, imported **last**, keyed on the attribute selector:
   ```less
   body[dir="rtl"] { direction: rtl; unicode-bidi: embed; }
   body[dir="rtl"] .pkp_site_name { text-align: right; }  /* + float/margin/position flips per breakpoint */
   ```
2. **bootstrap3:** runtime server-side detection to load a separate compiled RTL bundle:
   ```php
   if (Locale::getMetadata(Locale::getLocale())->isRightToLeft()) {
       $this->addStyle('bootstrap-rtl', 'styles/bootstrap-rtl.min.css');
   }
   ```
3. **Child themes** (defaultManuscript, healthSciences): ship their own `rtl.less` rather than relying on the parent's.

## 8. Theming the editorial backend (3.5)

- Officially supported but discouraged beyond brand colours: `addStyle('backend', 'styles/backend.css', ['context' => 'backend'])` and `modifyStyle('pkpLib', ['addLessVariables' => ...])`.
- The 3.5 editorial UI is Vue 3 + Tailwind; no official theme rewrites Vue components — backend theming = CSS/template injection around the Vue app, nothing more.
- Reader-facing frontend remains Smarty + LESS in 3.5; the ThemePlugin API did not change from 3.4.

## 9. Theme debugging checklist

1. Theme not listed → `version.xml` type/lazy-load/class-dir naming mismatch; check PHP error log for namespace errors.
2. Styles not updating → compiled LESS is cached: clear `cache/`, hard-reload.
3. Template edit invisible → wrong mirror path or stale `cache/t_compile/`.
4. Colour option does nothing → you overrode `@primary` but the option writes `@bg-base` (§3), or no `addLessVariables` re-injection in `init()`.
5. Option not applying → options are per-context, saved in Website Settings → Appearance; `getOption()` returns defaults only before first save.
6. RTL broken → ensure `rtl.less` imports last; verify `body[dir="rtl"]` actually set (locale metadata).

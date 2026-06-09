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

## 10. Building a complete custom theme — production lessons (all source-verified, 3.5)

Hard-won gotchas from building a full bespoke theme (standalone CSS, custom header/footer/homepage, dynamic data). Each caused a real bug.

**A re-uploaded plugin update silently does NOTHING unless you bump `<release>` in `version.xml`.** This is the #1 cause of "my fix didn't take effect / settings still look wrong" after re-installing. OJS compares the uploaded plugin's version with the installed one; if it is the **same or lower**, the Plugin Gallery upload is rejected/ignored and the **old files stay in place** — so none of your template/CSS/option changes appear and the admin keeps seeing the previous (e.g. empty/broken) build. Increment the four-part version for **every** rebuild you want installed (`1.0.1.0` → `1.0.2.0` → …), re-upload, then **Clear Data Caches**. When iterating, treat "bump version.xml" as part of every package step, not an afterthought.

**Multilingual theme-option fields read as empty in the settings form** even though the rest works — see the dedicated multilingual section: a multilingual field needs a **locale-keyed default object** (a scalar leaves it blank), and to never show a blank tab, fill **every** supported locale (`$ctx->getSupportedLocales()`), not just `en`.

**Locale: `##plugins.themes.x.key##` showing on the live site.**
- Symptom: every theme string renders as `##key##` while core English works.
- Cause: OJS does **not** rebuild the compiled locale cache when a plugin is installed. The keys load fine, the cache is just stale.
- Fix: **Administration → Clear Data Caches** (deletes `cache/fc-*`). This is the #1 post-install support answer.
- Folder MUST be the short code: `locale/en/locale.po`, `locale/ar/locale.po` (not `en_US`). `Plugin::addLocaleData()` registers the `locale/` dir via `Locale::registerPath()`; it runs from `LazyLoadPlugin::register()` (line 37), which `ThemePlugin` inherits — so no manual call needed.
- `.po` must be valid gettext: balanced `msgid`/`msgstr`, and **escape inner quotes** (`\"Spectral\"`) or loading silently fails. Validate with `msgfmt -c` (NOT a line counter).
- **CRITICAL — put a blank line between every entry.** OJS 3.5's PO loader separates entries on blank lines; consecutive `msgid`/`msgstr` pairs with *no* blank line between them get silently dropped, keeping only the **last** entry of each blank-line-delimited block. Symptom: a *positional* `##key##` pattern where only the last option in each section resolves and the rest show `##` (looks like a partial cache miss but isn't). Match the default theme: one blank line after every entry. Real fix that caused this: a hand-written `.po` with no inter-entry blank lines.

**Removing the default stylesheet drops base utility CSS.** A child theme that does `removeStyle('stylesheet')` (to ship its own CSS) loses utilities the default sheet provided — most visibly **`.cmp_skip_to_content`** (the skip links become *visible text* at the top of every page) and `.pkp_screen_reader` / `.pkp_helpers_display_none`. Re-add them:
```css
.cmp_skip_to_content a{position:absolute;inset-inline-start:-2000px;width:1px;height:1px;overflow:hidden;}
.cmp_skip_to_content a:focus{inset-inline-start:0;width:auto;height:auto;overflow:visible;}
.pkp_screen_reader{position:absolute!important;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;}
.pkp_helpers_display_none{display:none!important;}
```

**Header/footer wrapper contract** (must match exactly or pages break). Header opens: `<body>` → `pkp_structure_page` → `pkp_structure_head`(header) → nav → `pkp_structure_content` → `pkp_structure_main`. Footer closes: `pkp_structure_main` → (sidebar) → `pkp_structure_content` → footer wrapper → `pkp_structure_page` → `</body>`. Include `headerHead.tpl` (it emits the whole `<head>`; don't add your own) and `skipLinks.tpl`. Capture `homeUrl` yourself (`{url page="index" router=PKP\core\PKPApplication::ROUTE_PAGE}`) — it is **not** a global.

**Sidebar layout via the `.has_sidebar` modifier**, not `:has()`. Core adds `has_sidebar` to `pkp_structure_content` when a sidebar exists; key your grid off it. To suppress the footer's block-sidebar on a page with its own bespoke sidebar, `{assign var="isFullWidth" value=true}` **before** the header include (footer checks `{if empty($isFullWidth)}`). Render admin block plugins yourself with `{capture}{call_hook name="Templates::Common::Sidebar"}{/capture}`.

**Dynamic navigation + footer from OJS menus.** Primary nav: `{load_menu name="primary" id="navigationPrimary" ulClass="..."}` (outputs `<ul class="pkp_nav_list"><li><a>`). Register extra areas in `init()` with `$this->addMenuArea(['footerCol1','footerCol2'])`; they become assignable in Settings → Website → Navigation. `{load_menu name=$area}` returns `''` when no menu is assigned → fall back to option links.

**Dynamic homepage stats** via Repo collectors (run only on the homepage template; guard null context — the issue collector throws without a context id):
```php
$articles = Repo::submission()->getCollector()->filterByContextIds([$id])
    ->filterByStatus([PKPSubmission::STATUS_PUBLISHED])->getCount();
$issues = Repo::issue()->getCollector()->filterByContextIds([$id])->filterByPublished(true)->getMany();
```
Gotcha: the **issue collector `orderBy` takes no direction** (ORDERBY_DATE_PUBLISHED is hardcoded DESC) — compute the earliest year with `min()` in PHP, not `limit(1)`.

**Rich-text + hyperlinks in theme options.** `FieldRichTextarea` works as a theme option (verified: no allow-list in `ThemePlugin::addOption`; core `PKPMastheadForm` uses it without `uploadUrl`). Defaults give a `link` button. Output with **`|strip_unsafe_html`** (HTMLPurifier; allows `<a href>`,`<p>`,`<strong>`,`<ul>`, strips `<script>`) — never `|escape` (shows literal HTML) or raw (XSS). Do **not** add the `image` plugin without a valid `uploadUrl`.

**Multilingual theme options** (verified working; no core theme uses it but the chain is fully wired): set `isMultilingual` on the field — either `addOption('x','FieldRichTextarea',['isMultilingual'=>true])` or, post-hoc for many, `$this->options['x']->isMultilingual = true;` in a loop after the `addOption` calls. `PKPThemeForm` renders per-locale tabs, the PUT `/contexts/{id}/theme` save (`ThemePlugin::saveOption`) stores the locale-keyed array as JSON (`setting_type=object`), and `getOptionValues` reconstructs it. Retrieve with **`$this->getLocalizedOption('x')`** (NOT `getOption`, which returns the raw `['en'=>…,'ar'=>…]` array). Make the getter robust: fall back to the raw scalar when the localized value is empty, so single-value defaults and pre-multilingual saved values still render:
```php
$ml = function($k){ $v=$this->getLocalizedOption($k); if($v===null||$v==='' ){$r=$this->getOption($k); if(is_string($r))$v=$r;} return (string)$v; };
```
Keep colours/fonts/toggles/URLs/numbers single-value; make only user-facing TEXT multilingual.

**CRITICAL multilingual-default gotcha (causes "all fields blank" in the settings form).** A multilingual field's default **must be a locale-keyed array**, not a scalar — otherwise the settings form renders an **empty** input. Why: `PKPThemeForm` sets each field's `value` from `getOptionValues()` (saved value, or `null` if unsaved), and `Field::getConfig()` does `value ?? default`. So for an unsaved option the form falls back to `->default`. A multilingual Vue field binds to an object like `{"en":"…"}`; given a scalar string it can't map it to any locale tab and shows nothing. (Non-multilingual fields with scalar defaults pre-fill fine — which is why only the multilingual ones look blank.) Fix: when you flip `isMultilingual`, wrap the default too. The render path (`getOption`/`getLocalizedOption`) works with a scalar, so this is purely for the form UI:
```php
$ctx = Application::get()->getRequest()?->getContext();
$supported = $ctx ? $ctx->getSupportedLocales() : ['en'];   // fill EVERY tab
foreach ($multilingualKeys as $k) {
    $opt = $this->options[$k]; $opt->isMultilingual = true;
    if (is_string($opt->default) && $opt->default !== '') {
        $base = $opt->default; $obj = [];
        foreach ($supported as $loc) { $obj[$loc] = ($loc === 'ar' && isset($ar[$k])) ? $ar[$k] : $base; }
        $obj['en'] = $obj['en'] ?? $base;
        $opt->default = $obj;
    }
}
```
**Seed every supported locale, not just `en`** — a multilingual field shows blank in any locale missing from the default object, so an `en`-only default looks empty when the admin opens (or the journal's primary is) the Arabic tab. Use the journal's real locales (`$ctx->getSupportedLocales()`), putting translated strings where you have them and the base value elsewhere. Empty-string defaults stay scalar (those are optional "leave blank to use journal data" overrides, intentionally blank).

**Locale switcher also on the site index (`.../index/{locale}`).** Build the toggle for the main OJS platform/site index too, where there is **no** journal context: source the locales from the site, not just the context — `$locales = $context ? $context->getSupportedLocaleNames() : $request->getSite()->getSupportedLocaleNames();` (both expose `getSupportedLocaleNames()`), and keep only the `PKPPageRouter` guard. `$router->url($request, null, $page, $op, $path, urlLocaleForPage: $code)` then produces correct site-level URLs.

**Locale switcher link — 3.5 embeds the locale in the URL; `user/setLocale` is GONE.** OJS 3.5 removed the `user` page handler entirely (`pages/user/UserHandler.php` no longer exists), so the old `{url page="user" op="setLocale" path=$loc source=…}` link **404s / silently fails** — a real, easy-to-miss bug when porting a 3.3/3.4 theme. The 3.5 mechanism is URL-embedded locale: the `{url}` Smarty function (and `PKPPageRouter::url`) take a **`urlLocaleForPage`** parameter. Because the requested *path args* are not exposed as a template variable (`$requestedPage`/`$requestedOp` are, `requestedArgs` is **not**), build the switch links in PHP from the `TemplateManager::display` hook, mirroring PKPTemplateManager's own hreflang logic, and assign them for the template to iterate:
```php
$request = Application::get()->getRequest();
$router  = $request->getRouter();
$context = $request->getContext();
if ($context && $router instanceof \PKP\core\PKPPageRouter
    && count($locales = $context->getSupportedLocaleNames()) > 1) {
    $page = $router->getRequestedPage($request);
    $op   = $router->getRequestedOp($request);
    $path = $router->getRequestedArgs($request);          // array — the missing template var
    $cur  = \PKP\facades\Locale::getLocale();
    $out  = [];
    foreach ($locales as $code => $name) {
        $out[] = ['code'=>$code, 'name'=>$name, 'current'=>$code===$cur,
                  'url'=>$router->url($request, null, $page, $op, $path, urlLocaleForPage: $code)];
    }
    $templateMgr->assign('myLocaleToggle', $out);          // {foreach}…<a href="{$loc.url|escape}">
}
```
`$supportedLocales` IS a frontend template var (a `code=>name` map from `getSupportedLocaleNames(LANGUAGE_LOCALE_ONLY)`), but it only gives names — it can't build a same-page switch URL on its own. There is no `languageToggle.tpl` include.

**Overriding frontend object/page templates — parity checklist (each omission is a real regression).** When you replace `article_summary`/`issue_toc`/`article_details`/`indexJournal` with bespoke markup, you inherit the handler's assigned vars but must keep the *logic*, or live data silently disappears:
- **`galley_link.tpl` marks every galley `restricted` unless `hasAccess` is truthy in scope.** In `article_details` the handler assigns a global `$hasAccess`, so an include works. In a **TOC/list** (`article_summary`), there is no per-article `$hasAccess` — you must compute it and pass it, or open-access downloads get a `.restricted` class + a "subscription access" screen-reader label: `{assign var=hasArticleAccess value=$hasAccess}{if $currentContext->getData('publishingMode')==APP\journal\Journal::PUBLISHING_MODE_OPEN || $publication->getData('accessStatus')==APP\submission\Submission::ARTICLE_ACCESS_OPEN}{assign var=hasArticleAccess value=1}{/if}` then `{include … hasAccess=$hasArticleAccess purchaseFee=$currentJournal->getData('purchaseArticleFee') purchaseCurrency=$currentJournal->getData('currency')}`.
- **Respect per-article author hiding:** `{if (!$section.hideAuthor && $publication->getData('hideAuthor')==APP\submission\Submission::AUTHOR_TOC_DEFAULT) || $publication->getData('hideAuthor')==APP\submission\Submission::AUTHOR_TOC_SHOW}` — not just `$section.hideAuthor`.
- **Filter TOC galleys to primary files** with `$primaryGenreIds` (skip dependent/supplementary): `{if $primaryGenreIds}{assign var=file value=$galley->getFile()}{if !$galley->getData('urlRemote') && !($file && in_array($file->getGenreId(),$primaryGenreIds))}{continue}{/if}{/if}`.
- **`indexJournal` must call `{call_hook name="Templates::Index::journal"}`** (homepage plugins/carousels hook here) **and render `{$additionalHomeContent}`** (the admin's Settings → Website → Appearance → *Additional Content*) — both are trivially dropped when you rewrite the homepage, silently discarding admin content and breaking plugins.
- **Highlights / spotlights (3.4+) are also dropped** if you rewrite `indexJournal`/`indexSite` — re-add `{if $highlights && $highlights->count()}{include file="frontend/components/highlights.tpl" highlights=$highlights}{/if}`. The core `highlights.tpl` is a **Swiper** carousel (needs Swiper JS+CSS the default theme bundles). A custom theme that doesn't ship Swiper should **override `highlights.tpl`** with a static layout (a card grid) so it works with zero JS — otherwise the slides stack unstyled and the prev/next buttons are dead. Highlight accessors: `getImage()`/`getImageUrl()`/`getImageAltText()`, `getLocalizedTitle()`, `getLocalizedDescription()`, `getUrl()`, `getLocalizedUrlText()`.
- **Site index (`indexSite`, multi-journal) realities:** the site `$about` is full rich CMS HTML with its own H2/H3 sections — render it as **`.prose`** at a readable measure, not oversized lead text. Each journal's `getLocalizedDescription()` is the **journal's entire description** (can be many paragraphs), so a journal-card list becomes a wall of text — **clamp** it (`max-height` + a fade-out `::after` gradient to `var(--card)`, or `line-clamp`) and let "View Journal" lead to the full text. There is no journal context here, so the masthead falls back to `$siteTitle` and the locale toggle must use site locales (see the locale-switcher note).
- **Handler-assigned vars worth preserving:** `$categories`, `$ccLicenseBadge` + `$currentContext->getLocalizedData('licenseTerms')` (copyright block), `$pubIdPlugins` (URN etc.), `$issueGalleys` (full-issue PDF on the issue page), `$userGroupsById` (author role labels), `array_reverse($article->getPublishedPublications())` (version history). `$dateFormatShort`/`$dateFormatLong` are PHP `date()` formats (use with `|date_format` or `DateTime::format`). To keep one `issue_toc.tpl` for both the homepage and the issue page, gate the issue-only chrome (cover, identifiers, full-issue galleys, publish date) behind a `hideCover` flag you pass from the homepage include.
- **Academic author/affiliation formatting:** for numbered-superscript authors with a numbered affiliation list, build the map in PHP (iterate `$author->getAffiliations()`, dedupe by `getLocalizedName()` in order of appearance, assign 1-based numbers, expose each author's `numStr` and each affiliation's `getRor()` for a ROR link), then render — far cleaner than trying to dedupe in Smarty. `getAffiliations()` is an entity array; `getLocalizedAffiliationNamesAsString(null, ', ')` is the quick inline alternative.
- **Inline PDF viewing is NOT a theme concern.** There is no core `articleGalley.tpl` to override — PDF galleys are embedded by the bundled **`pdfJsViewer`** generic plugin (it hooks the galley view and ships its own viewer template). Don't reinvent a PDF embed in the theme; just enable/style around that plugin. (HTML galleys are styled via your `['contexts'=>'htmlGalley']` stylesheet.)
- **Article-page elements easy to miss:** the **article's own cover image** (`$publication->getLocalizedData('coverImage')` → array with `.altText`; URL via `$publication->getLocalizedCoverImageUrl($article->getData('contextId'))`); **non-DOI pub-IDs** (loop `$pubIdPlugins`, skip `getPubIdType()=='doi'`, `$publication->getStoredPubId($type)`, link via `$pubIdPlugin->getResolvingURL($currentJournal->getId(), $pubId)`); and **ORCID** — core assigns `$orcidIcon` / `$orcidUnauthenticatedIcon` (ready-made markup) and `$author->hasVerifiedOrcid()`, so render the real ORCID logo (verified vs not) rather than a text "iD". For brand **share icons** (X/LinkedIn/Facebook) use inline SVG brand paths, not letters/emoji.
- **`article_summary.tpl` is used from THREE places** — issue TOC, homepage current-issue TOC, and the search results page (`search.tpl` includes it as `article=$result.publishedSubmission journal=$result.journal showDatePublished=true hideGalleys=true`). A bespoke override must therefore: honour **`$hideGalleys`** (search hides them); honour **`$journal`** for cross-journal links — `{url journal=$journal->getPath() page="article" …}` and pass `journalOverride=$journal` to `galley_link.tpl`; and handle the **no-`$currentContext`** case (site-wide search) by showing `getLocalizedFullTitle()` + the source journal name instead of `getLocalizedTitle()`. Miss these and a multi-journal search links to the wrong journal and shows galleys it meant to hide.

`source` (the old 3.3/3.4 approach, for reference only): had to be host+URI, unescaped.

**A theme that ships its own CSS (`removeStyle('stylesheet')`) must bridge the core DOM of pages it does NOT override** — they still render through your header/footer but with core markup. Verified gaps that look broken without bridge rules (page wrappers are `.page_<op>`):
- **Issue archive** (`issueArchive.tpl`, `.page_issue_archive`) lists issues as `<ul class="issues_archive"><li>{issue_summary}</li>` — needs a grid + `list-style:none` or you get a single-column bullet stack. To **group by volume** (a common request — there is no separate "volume" page), the `$issues` array is newest-first so volumes are contiguous: track `$issue->getVolume()`, and when it changes close the open `<ul>` and emit a `<h2>Volume N (Year)</h2>` + new `<ul>` (open the first `<ul>` on the first non-matching item, close on `$smarty.foreach.x.last`). Grouping is per-page (the archive is paginated), which is fine.
- **Editorial masthead / history** (`editorialMasthead.tpl` `.page_masthead`, `editorialHistory.tpl`) render contributors as `<ul class="user_listing">` with `.name`/`.affiliation`/`.orcid`/`.date_start` — **zero** default styling; bridge to a card grid.
- **Announcements list** (`announcements.tpl` `.page_announcements`) renders core `.obj_announcement_summary` (+`_image`, `.date`, `.summary`) — your homepage's bespoke announcement markup does **not** apply here.
- **Category browse** (`catalogCategory.tpl`) wraps articles in `<ul class="cmp_article_list">` — needs the list reset.
- **Contact** (`.page_contact`) → `.contact_section > .address / .contact.primary / .contact.support` with `.name/.title/.affiliation/.phone .label|.value/.email`; **search** (`.page_search`) → `.cmp_form`, `button.submit`, `.search_advanced`, `<ul class="search_results">`, `.cmp_pagination`; **login/register** are `userLogin.tpl`/`userRegister.tpl` (`.cmp_form.login`).
- **Shared components** included across many pages (and by your own object templates): `notification.tpl` emits `<div class="cmp_notification {warning|error|notice}">` — style the base **and** the variants, or the issue-preview banner, "no current issue", and search errors render as unstyled plain text (styling only `.notice` misses `warning`/`error`). `breadcrumbs.tpl` is `<nav class="cmp_breadcrumbs"><ol><li><a>…</a><span class="separator">…</span></li><li class="current"><span aria-current>…</span></li></ol>`. `pagination.tpl` → `.cmp_pagination` with `.prev/.current/.next`. The announcements **list** wraps items in `<ul class="cmp_announcements">` (needs a list reset).
- **Complete frontend template inventory (3.5)** so a "ship-everything" theme misses nothing. `pkp-lib/templates/frontend/objects/`: `announcement_full`, `announcement_summary`, `announcements_list`. `ojs/…/objects/`: `article_details`, `article_summary`, `galley_link`, `issue_summary`, `issue_toc`. `pkp-lib/…/components/`: `header`, `headerHead`, `footer`, `breadcrumbs`(+`_announcement`,`_catalog`), `navigationMenu` + `navigationMenus/dashboardMenuItem`, `highlights`, `pagination`, `editLink`, `registrationForm`, `registrationFormContexts`, `announcements`. `ojs/…/components/`: `primaryNavMenu`, `breadcrumbs_article`, `breadcrumbs_issue`, `notification`, `skipLinks`, `subscriptionContact`.
- **Nav menus:** `{load_menu name="primary"}` renders `navigationMenu.tpl` → `<ul class="pkp_nav_list"><li><a>…</a><ul>…children…</ul></li>` when a custom menu is assigned, else falls back to `primaryNavMenu.tpl` (`<ul class="pkp_navigation_primary pkp_nav_list">` with an *About* dropdown). Style structurally (`.nav ul`, `.nav ul ul`) so both forms work.
- **Registration is two components, not one cmp_form layout:** `registrationForm.tpl` (fieldsets `.identity`/`.login`, each `.fields > div.given_name|.family_name|.affiliation|.country|.email|.username|.password`, every field `<label><span class="label">…<span class="required">*</span></span><input></label>`) and, on the **site-wide** register (no `$currentContext`), `registrationFormContexts.tpl` — a `<ul class="contexts"><li class="context"><div class="name"><fieldset class="roles"><label><input type=checkbox> role</label>…` role picker. Style `.fields .label`, the wrapping `<label>`, checkbox `<label>`s (flex, `input{width:auto}`), and `.contexts .context` as cards, or registration looks raw. **`editLink.tpl`** emits a manager-only `<a class="cmp_edit_link">` next to section titles on about/contact/submissions/information — give it a small badge style.

**3.5 page-template names & locations** (so you grep the right file): app-level in `pkp/ojs/templates/frontend/pages/` = `indexJournal`, `indexSite`, `article`, `issue`, `issueArchive`, `search`, `catalogCategory`, `submissions`; shared in `pkp/pkp-lib/templates/frontend/pages/` = `about`, `contact`, `announcements`/`announcement`, `editorialMasthead`, `editorialHistory`, `information`, `privacy`, `error`, `userLogin`, `userRegister`, `userLostPassword`. The "Editorial Team" page became **`editorialMasthead`** in 3.4+. None of `article`/`issue`/`search` set `$isFullWidth`, so a bespoke object template carrying its own sidebar coexists with the block-plugin sidebar. If your `article_details` has its **own** two-column grid (main + details sidebar) and you want that to be the *only* layout (no cramped third column), **override `article.tpl` and `{assign var="isFullWidth" value=true}` before the header include** — that suppresses the outer block sidebar so the article's grid is exactly two columns. (Trade-off: block plugins won't show on the article page.) There is no "volume" page in OJS — volume/number/year are the *issue* identification (`$issueIdentification`); the single-issue landing is `issue.tpl` (h1 + `issue_toc`).

**You cannot turn the theme-settings form into tabs from the theme.** Theme options render in OJS's core **Appearance → Theme** `PKPThemeForm`, which puts every `addOption` field in one flat default group — a plugin can't add tabs/pages/section headers there (it's core Vue UI). The lever you *do* have is **more options**: colours (`FieldColor`), selects (`FieldOptions` radio), text/number (`FieldText`), textareas, rich text, multilingual text — group them logically by registration order and clear labels. For deeper layout control, ship CSS variables + a `customCss` escape hatch rather than trying to re-skin the admin form.

**When you DO override a page template, copy the fragile bits verbatim and only reskin the shell.** `search.tpl` is the prime example: keep `{html_select_date_a11y …}`, the `{capture name="searchFormUrl"}…|parse_url|parse_str` dance, `{iterate from=results}`, `{page_info}`/`{page_links …}` (with every `dateFrom*`/`dateTo*` arg) and both `Templates::Search::*` hooks exactly as core has them — wrap only the surrounding markup. Same for `issueArchive` (`{include …/pagination.tpl}` + prev/next URL capture) and `contact` (`{mailto encode='javascript'}`). For **auth pages** (`userLogin`/`userRegister`/`userLostPassword`) skip the override entirely — their forms are long and fragile (csrf, reCAPTCHA/altcha, many fields). Brand them with **CSS only**, keyed off the `.page_login`/`.page_register`/`.page_lostPassword` wrappers: centre the `.cmp_form` in a narrow card. Single-announcement detail renders through `frontend/objects/announcement_full.tpl` (override the object, not just the thin page).

**The `core:` template prefix bypasses theme overrides — watch for it.** OJS's app-level `submissions.tpl` does `{capture …}{/capture}` then `{include file="core:frontend/pages/submissions.tpl"}`; the `core:` prefix forces the pkp-lib copy, *ignoring* your theme's same-named file. So putting `templates/frontend/pages/submissions.tpl` in your theme does NOT reskin the rendered output — your file replaces the thin app wrapper, but the `core:` include still pulls the unstyled pkp-lib body. To actually reskin such a page, **inline** the core body in your override (re-implement its sections) rather than re-including `core:`. For `submissions` that means rebuilding the submission-actions notice, author guidelines, preparation checklist, per-section policies (`$sections` → `getLocalizedPolicy()`), copyright notice and privacy statement, each with its `editLink`. Grep core templates for `file="core:` to find every page that uses this pattern.

**Theme-added SEO / Open Graph meta.** Core emits article `citation_*` (Google Scholar) + Dublin Core meta via indexing plugins through `{load_header}` (in `headerHead.tpl`) and the `Templates::Article::Main` hook — preserve both. Add journal-level OG/Twitter/description yourself from the `TemplateManager::display` hook (fires before `headerHead` renders), keyed so they don't duplicate:
```php
$templateMgr->addHeader('ogTitle', '<meta property="og:title" content="'.htmlspecialchars($name).'">');
```
Core ships **no schema.org JSON-LD** — adding it is a real rich-results win for a scholarly site. From the same `TemplateManager::display` hook, branch on `$template`: emit a `ScholarlyArticle` graph on `frontend/pages/article.tpl` and a `Periodical` graph on `frontend/pages/indexJournal.tpl`. Pull the objects from the already-assigned template vars — `$templateMgr->getTemplateVars('publication')` / `'article'` / `'issue'` (the handler assigns them before display). Build a plain array (headline, author[] with affiliation+ORCID `identifier`, datePublished, abstract, keywords, `isPartOf` Periodical+ISSN, publisher, `identifier`/`sameAs` = the DOI resolving URL), `json_encode($d, JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE)`, then `str_replace('</','<\/',$json)` (can't break out of `<script>`) and `addHeader('jsonLd', '<script type="application/ld+json">'.$json.'</script>')`. Wrap it all in try/catch — it's purely additive and must never fatal the page. Two cheap wins from the same hook: a self-referencing **`rel="canonical"`** with the query string stripped (`strtok($request->getCompleteUrl(), '?')`) — `getCompleteUrl()` keeps tracking/sort params, which canonical should not — and `loading="lazy" decoding="async"` on below-the-fold `<img>` in your object templates (issue covers, thumbnails, announcement/highlight images), keeping the masthead logo eager for LCP. A matching theme convenience is an **auto "How to cite"** block: core only emits a citation when the **Citation Style Language** plugin is enabled, so building a simple APA string yourself from the publication metadata (authors → `getLocalizedData('familyName'/'givenName')` initials, year from `datePublished`, title, journal `getLocalizedName()`, `$issue->getVolume()/getNumber()`, `getData('pages')`, DOI resolving URL) and rendering it with a copy button is a high-value, self-contained add (pass it as a template var from the article-template branch of the hook). Offer **BibTeX/RIS download** with no server endpoint via `<a download href="data:application/x-bibtex;charset=utf-8,{$bib|escape:'url'}">` (build the `.bib`/`.ris` strings in PHP from the same metadata; BibTeX page ranges use `--`). A **"More from this issue"** sidebar list comes from `Repo::submission()->getCollector()->filterByContextIds([$id])->filterByIssueIds([$issue->getId()])->filterByStatus([STATUS_PUBLISHED])->getMany()` (exclude the current `$article->getId()`, cap ~5). Add a **`BreadcrumbList`** JSON-LD too (Home → Issue → Article) — build the item URLs with `$request->getDispatcher()->url($request, PKPApplication::ROUTE_PAGE, $context->getPath(), 'issue', 'view', [$issue->getBestIssueId()])`. And surface the **issue cover** (`$issue->getLocalizedCoverImageUrl()`) as a thumbnail in the article sidebar linking back to the issue. Give the JSON-LD `publisher` Organization a **logo** `ImageObject` for knowledge-panel eligibility — build the URL from the assigned template vars `displayPageHeaderLogo['uploadName']` + `publicFilesDir` (don't hand-roll the public-files path). For accessibility beyond `prefers-reduced-motion`, add **`@media (prefers-contrast: more)`** (darken muted text/lines, underline links) and **`@media (forced-colors: active)`** (give buttons/cards `1px solid CanvasText`, use `Highlight` for the active nav/progress bar, hide decorative watermarks) — Windows High-Contrast users otherwise lose your borders. On the journal home, emit a **`WebSite` + `SearchAction`** node (in a `@graph` alongside the `Periodical`) so Google can show a sitelinks search box — `urlTemplate` = the OJS search URL (`$dispatcher->url(..., 'search', 'search')`) + `?query={search_term_string}`, with `'query-input' => 'required name=search_term_string'`.

**Social-card image + per-page OG (extends the JSON-LD block above).** Give the `ScholarlyArticle` JSON-LD an **`image`** and make `og:image`/`twitter:image` resolve to the real artwork, with a three-step fallback: the **article's own cover** (`$publication->getLocalizedData('coverImage')` is a `['uploadName'=>…]` array when set → `$publication->getLocalizedCoverImageUrl($context->getId())`), else the **issue cover** (`$templateMgr->getTemplateVars('issue')?->getLocalizedCoverImageUrl()`, no contextId arg), else the journal-level `seoImage` option. Do the same probe in `addSeoMeta()` so article/issue pages get a `summary_large_image` Twitter card and the cover as `og:image`; on those pages also switch `og:type` to `article` and set `og:title`/`twitter:title` to the **paper's** title (`$pub->getLocalizedTitle()`) instead of the journal name (guard with `method_exists`/`getTemplateVars('publication')` since the same method runs on every page). Once `og:type=article`, emit the **article-specific OG properties** scrapers expect: `article:published_time` (`$pub->getData('datePublished')`), `article:section` (`getTemplateVars('section')->getLocalizedTitle()`), and one `article:tag` per keyword (cap ~10; keywords are objects/arrays with a `name` — handle `is_object`/`is_array`/string defensively, same as the JSON-LD branch). All purely additive.

**Overriding `galley_link.tpl` (the one core *object* worth re-skinning).** A child-of-default theme inherits every non-overridden template, so the download/view buttons render through the parent's `frontend/objects/galley_link.tpl`. To brand them (file-type icon + button styling) **copy the core template verbatim and reskin only the markup** — its logic is fragile: `$journalOverride` reassigns `$currentJournal`; `$galley->isPdfGalley()` → `pdf`/`file` type; the issue-vs-article `$page`/`$path` computation includes the **versioned** path (`…|to_array:"version":$publication->getId():…` when `$publication->getId() !== $parent->getData('currentPublicationId')`); the `$restricted` flag derives from `$hasAccess`/`$restrictOnlyPdf`; and the screen-reader subscription/fee text + `purchase_cost` (`reader.purchasePrice`) must stay. Keep the core classes (`obj_galley_link` / `obj_galley_link_supplementary` / `pdf` / `restricted`) so parent CSS and galley JS still match; add your own (`galley-btn`, `.galley-ico` SVG). Pick the icon off the same `$type` var (pdf vs generic download) plus `$galley->getRemoteUrl()` for an external-link mark — don't try MIME-substring matching in Smarty (no safe `strstr` modifier under OJS's security policy). No new locale keys needed — it reuses core `reader.*` keys.

**Overriding `article_details` is Google-Scholar-safe.** The `citation_*` (Highwire/Scholar) and Dublin Core `<meta>` are **not** in `templates/frontend/objects/article_details.tpl` — they're emitted into `<head>` by the core article handler / indexing plugins via `addHeader` + `{load_header}`. So a fully bespoke `article_details.tpl` (body only) does **not** drop Scholar indexing; just keep the `Templates::Article::Main` and `Templates::Article::Details` hooks for plugins (altmetrics, Paperbuzz, usageStats, CSL "How to cite") to inject. Full app-level page list to know what's inheritable vs. overridden: `aboutThisPublishingSystem, article, catalogCategory, indexJournal, indexSite, issue, issueArchive, search, submissions` **plus** the subscription set `purchaseIndividualSubscription, purchaseInstitutionalSubscription, subscriptions, userSubscriptions` — the latter only render for paid/subscription journals, so an OA theme can safely leave them on the parent and document it rather than building them.

**Custom CSS escape hatch.** Expose a `customCss` `FieldTextarea`, inject inline with high priority so it wins: `$this->addStyle('customCss', $css, ['inline'=>true, 'priority'=>999])`. Strip `</style>`/`<script>` defensively. Inline styles emit in priority then registration order (`ksort`); default priority is `STYLE_SEQUENCE_NORMAL` (10), so 999 = last. See rest-api/architecture refs for the data-layer 3.5 gotchas a theme also hits: Announcement is Eloquent (`->datePosted->format($dateFormatShort)`, `getLocalizedData('title')`, `->id`), keywords are objects (`$keyword.name`), affiliations are entities (`$author->getAffiliations()`), DOI display uses `getData('doiObject')->getData('resolvingUrl')`, and `article_details` must use the **viewed** `$publication` (not `getCurrentPublication()`) or old-version views show the current version.

**Stylesheet packaging gotchas (from a full theme audit).**
- **`htmlGalley` context CSS is isolated.** A stylesheet registered with `addStyle('x','htmlGalley.css',['contexts'=>'htmlGalley'])` is applied inside the inline HTML full-text galley, which renders in its **own** document — it does **not** inherit the main frontend stylesheet or its CSS custom properties. Make it self-contained: literal colours/fonts, **no `var(--…)`** (they resolve to nothing there). Mirror your palette as literal hex.
- **Relative `url()` in your own theme CSS resolves relative to the CSS file, not the page.** With `theme.css` at the plugin root and an `assets/` sibling, `url('assets/logo.png')` works from any page URL. (In a `<style>`-injected/inline block there is no base file, so use absolute `{$baseUrl}/…` there instead.)
- **Palette-from-one-colour via `color-mix()`.** Derive a whole scale from a few brand-colour options (`--navy-900:color-mix(in srgb, {$primary} 66%, #000)` …), and only emit the `:root{…}` override block when the option **differs from its default** — so the shipped defaults stay byte-identical to the reference design and you're not fighting your own cascade.
- **Sidebar two-column trigger: key off the rendered element, not just the flag.** The footer emits `.pkp_structure_sidebar` **only** when `Templates::Common::Sidebar` returns content, while the header adds `.has_sidebar` from `$hasSidebar`. Style the grid with `.pkp_structure_content:has(> .pkp_structure_sidebar){grid-template-columns:1fr 312px}` (default 1fr) so you never get an empty second column if the flag and content disagree; add the `.has_sidebar` selector alongside it only as a fallback for browsers without `:has()`. Both derive from the same block list, so in practice they agree.
- **If you build the locale switcher as `<a>` links** (per the 3.5 `urlLocaleForPage` approach above), style `.lang-toggle a` / `.lang-toggle a.current` — don't leave `button[aria-pressed]` rules from a 3.3-era markup that now match nothing.
- **Theme JavaScript:** register with `$this->addScript('x','js/x.js',['contexts'=>'frontend','defer'=>true])` (path is relative to the plugin root; it's emitted by `{load_script context="frontend"}` in `footer.tpl`). Best pattern for things like a mobile hamburger / back-to-top: **render the button(s) in the templates** (so their labels are translated via `{translate}`) and let the JS only wire behaviour + toggle classes — keeps it dependency-free and usable with JS off. Gate any smooth-scroll behind `matchMedia('(prefers-reduced-motion: reduce)')`. Note the default theme bundles **Swiper** for highlights; a theme that drops the default JS must not rely on Swiper-driven markup.
- **Dark mode that doesn't flash:** if your design system is built on CSS custom properties, dark mode is mostly a `:root[data-theme="dark"]{ … }` block that **remaps the neutral/paper/ink variables** (keep navy/brass scales — masthead/nav/footer are already dark) plus ~15 overrides for the spots that hard-code `#fff` or `navy-900` text. Set `data-theme` **in `<head>` before first paint** via a tiny inline `addHeader` script (`localStorage` choice → else `matchMedia('(prefers-color-scheme: dark)')`), or you get a white flash; a deferred footer script only handles the manual toggle's click + persistence. Make it an **admin choice** — a `FieldOptions` radio (`light` = no dark mode / `toggle` = visitor switch + remembers / `auto` = follow device, no button); the head script reads `localStorage` only in `toggle` mode and is omitted entirely for `light`. After building dark mode, **grep your CSS for every `color:var(--navy-900|800)` and `background:#fff`** — the variable remap misses any rule that hard-codes a dark text colour or white surface (titles, `.prose h3`, form labels/legends, `.mb-v`, contact/masthead-list names), so each needs an explicit `[data-theme="dark"] …{color:var(--ink)}` / `background:var(--card)` override or it goes dark-on-dark.
- **Context-aware chrome on the multi-journal site index.** `$currentContext` is null there, so journal-specific masthead bits — the "Make a Submission" CTA (submit to *which* journal?) and a journal-frequency meta line — should be gated with `{if … && $currentContext}`. The site index also falls back to `$siteTitle` for the name and needs the site-locale switcher. Keyboard-accessible dropdowns are free with `li:focus-within > ul{display:block}` (no JS). Privacy-friendly article sharing = plain intent links (`twitter.com/intent/tweet`, `linkedin.com/sharing/...`, `mailto:`) built from `{url}` + `|escape:"url"` — no third-party scripts; pair with a `navigator.clipboard` copy-link button.
- **Use inline SVG for UI icons, never Unicode dingbats.** Glyphs like ☀ (U+2600), ☾ (U+263E) and ⌕ (U+2315) render as **tofu/`?`** in serif/text fonts (Spectral, Amiri, etc. don't include them) — a real "the icon is broken" bug. Ship tiny inline `<svg fill="none" stroke="currentColor">` icons (sun/moon for the dark toggle, magnifier for search, chevron for back-to-top) so they inherit colour and always render. Basic typographic arrows (`→` U+2192, `↑` U+2191) are fine in text fonts, but anything in the Miscellaneous-Technical/Dingbats ranges is not. (Authoring note: write such templates with a real editor — non-ASCII glyphs piped through a PowerShell here-string get mangled.)
- **Ship an article print stylesheet (`@media print`).** Researchers print the HTML article page, not just the PDF. Hide the OJS/theme chrome by class — `.util-bar,.masthead,.nav,.pkp_structure_footer_wrapper,.index-strip,.sidebar,.pkp_structure_sidebar,.cmp_breadcrumbs,.cmp_skip_to_content` plus your own interactive bits (`.art-share,.theme-toggle,.nav-toggle,.to-top,.reading-progress,.obj_galley_link,.download-box`) — then flatten the article's `display:grid` to `display:block` so the two-column `.art-detail-grid` becomes one readable column. Force black-on-white, de-pill keyword/galley chips (`background:none;border:1px solid #999`), `page-break-inside:avoid` on `.references li`/`.abstract-block`, and expand link targets with `a[href^="http"]::after{content:" (" attr(href) ")"}` so citations survive on paper. Note the bespoke article sidebar is `<aside class="sidebar">`, so hiding `.sidebar` already drops its cover/download/issue widgets — don't add redundant per-element hides.
- **Respect real uploaded covers *everywhere*, not just the archive.** If the theme draws a stylised CSS "generated cover" (acronym + volume on a gradient) when no artwork exists, gate it on `{assign var=cover value=$issue->getLocalizedCoverImageUrl()}{if $cover}<img …>{else}…generated…{/if}` in **every** place a cover renders — homepage current-issue banner, homepage sidebar cover widget, archive card (`issue_summary.tpl`) **and** the issue landing (`issue_toc.tpl` with `hideCover=false`). It's easy to add the fallback to the archive card and forget the homepage, so a journal that uploads covers sees them on `/issue/archive` but a generated mark on the front page. For the real-image variant, reuse the `.cover` frame but zero its padding and fill it: `.cover.cover-real{padding:0}.cover.cover-real img{width:100%;height:100%;object-fit:cover;display:block}` (keep the `aspect-ratio:3/4` and the brass spine `::before` so both variants share one silhouette). Always pass `alt=$issue->getLocalizedCoverImageAltText()|default:$issue->getIssueIdentification()|strip_tags`.

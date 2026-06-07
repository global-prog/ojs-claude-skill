# OJS Frontend Templating Internals (3.5, with 3.4 notes)

Verified from `PKPTemplateManager.php`, frontend `.tpl` source, and handlers on `stable-3_5_0`. Companion to theme-development.md (themes) and hooks-catalog.md (hooks).

## 1. Smarty tags registered by PKPTemplateManager

**Functions:** `{translate key="..." param=$x}` · `{url page=... op=... path=...}` (dispatcher URL builder — always use this, never hand-build) · `{csrf}` · `{call_hook name="..."}` / `{run_hook}` · `{load_stylesheet context="frontend"}` · `{load_script context="frontend"}` · `{load_header context="frontend"}` · `{load_menu name="primary" id="..." ulClass="..." liClass="..."}` · `{load_url_in_div}` / `{load_url_in_el}` · `{title}` · `{help}` · `{page_links}` / `{page_info}` · `{pluck_files}` · `{locale_direction}` · `{html_options_translate}` · `{html_select_date_a11y}` · `{constant}` · `{flush}` · FBV form tags (`{fbvElement}`, `{fbvFormButtons}`, `{fieldLabel}`).

**Blocks:** `{iterate from=...}`, `{fbvFormSection}`, `{fbvFormArea}`.

**Modifiers (custom):** `|translate` · `|strip_unsafe_html` (→ `PKPString::stripUnsafeHtml`) · `|escape` (HTMLPurifier-aware override) · `|date_format` · `|json_encode_html_attribute` · `|String_substr` · `|to_array` · `|compare` · `|concat` — plus many PHP passthroughs (`count`, `explode`, `json_encode`, `array_key_exists`, …).

**NOT global tags in 3.5:** `{load_block}` does not exist (sidebar renders via hook, §4); `{plugin_url}` is not globally registered — it's available where a plugin registers it (e.g. import/export plugin templates via `ImportExportPlugin::pluginUrl`).

Custom Smarty tags from plugin/theme code: `$templateMgr->registerPlugin('function', 'my_tag', [$this, 'smartyMyTag'])` — `PKPTemplateManager extends Smarty`, so the standard Smarty API applies (core itself registers everything this way; no bundled plugin example exists).

## 2. Always-available template variables (frontend)

`$baseUrl` · `$currentContext` (journal; null on site pages) · `$currentLocale` · `$currentLocaleLangDir` (`ltr`/`rtl`) · `$applicationName` · `$requestedPage` / `$requestedOp` · `$currentUser` / `$isUserLoggedIn` / `$isUserLoggedInAs` / `$loggedInUsername` / `$unreadNotificationCount` · `$siteTitle` · `$displayPageHeaderTitle` / `$displayPageHeaderLogo` · date/time formats (`$dateFormatShort`, `$dateFormatLong`, …) · `$itemsPerPage` / `$numPageLinks` · `$activeTheme` · `$hasSidebar` (true when the context/site `sidebar` setting is non-empty) · `$pageTitleTranslated` (set per page).

**Article page** (`frontend/pages/article.tpl`, assigned by `ArticleHandler::view`): `article`, `publication`, `currentPublication`, `firstPublication`, `issue`, `section`, `categories`, `galley`, `primaryGalleys`, `supplementaryGalleys`, `submissionFileId`, `parsedCitations`, `licenseTerms`, `licenseUrl`, `ccLicenseBadge`, `copyrightHolder`, `copyrightYear`, `keywords`, `pubIdPlugins`, `userGroupsById`, `orcidIcon`, `rorIdIcon`, `hasAccess`, `purchaseArticleEnabled`.

**Issue page** (`frontend/pages/issue.tpl` via `IssueHandler`): `issue`, `issueId`, `issueIdentification`, `issueTitle`, `issueSeries`, `issueGalleys`, `publishedSubmissions`, `primaryGenreIds`, `authorUserGroups`, `hasAccess`, `purchaseArticleEnabled`, subscription partials when gated.

Reading/adding template data from a plugin: hook `TemplateManager::display`, guard on `$args[1] === 'frontend/pages/article.tpl'`, use `$templateMgr->getTemplateVars('issue')` / `assign()`. **Limitation:** only top-level `frontend/pages/*` templates fire the hook usefully — included sub-templates don't re-fire it.

## 3. Template inventory (what exists to override)

**pkp-lib `templates/frontend/pages/`**: about, announcement(s), contact, editorialHistory, editorialMasthead, error, information, message, navigationMenuItemViewContent, orcidAbout, orcidVerify, privacy, submissions, userConfirmActivation, userLogin, userLostPassword, userRegister, userRegisterComplete.

**pkp-lib `objects/`**: announcement_full, announcement_summary, announcements_list. **pkp-lib `components/`**: header, headerHead, footer, breadcrumbs (+ variants), navigationMenu, pagination, announcements, highlights, editLink, registrationForm(+Contexts), skip-link infra, `navigationMenus/dashboardMenuItem.tpl`.

**OJS `pages/`**: article, issue, issueArchive, indexJournal, indexSite, search, catalogCategory, aboutThisPublishingSystem, submissions, subscriptions, userSubscriptions, purchaseIndividual/InstitutionalSubscription. **OJS `objects/`**: article_details, article_summary, galley_link, issue_summary, issue_toc. **OJS `components/`**: breadcrumbs_article, breadcrumbs_issue, notification, primaryNavMenu, skipLinks, subscriptionContact.

## 4. Header, footer, sidebar machinery

**`header.tpl`**: `<html lang="{$currentLocale|replace:"_":"-"}">`; includes `headerHead.tpl` (`{load_header}` + `{load_stylesheet}` live there) and `skipLinks.tpl`; `<body class="pkp_page_{$requestedPage} pkp_op_{$requestedOp}" dir="{$currentLocaleLangDir}">`; loads menus: `{load_menu name="primary" id="navigationPrimary" ulClass="pkp_navigation_primary"}` + `{load_menu name="user" ...}`.

**`footer.tpl`**: renders the sidebar — `{capture assign="sidebarCode"}{call_hook name="Templates::Common::Sidebar"}{/capture}` wrapped in `.pkp_structure_sidebar` (skipped when `$isFullWidth`); then `{load_script context="frontend"}` and `{call_hook name="Templates::Common::Footer::PageFooter"}`.

**Sidebar blocks (3.5 verified pipeline):** there is no per-block hook registration. `PKPTemplateManager::initialize()` registers `displaySidebar()` on `Templates::Common::Sidebar`; it reads the ordered array of block plugin names from the **context (or site) `sidebar` setting**, loads `PluginRegistry::loadCategory('blocks', true)`, and concatenates each `getContents($templateMgr, $request)`. Block order = array order in that setting (managed in Website Settings → Appearance → Setup → sidebar). `BlockPlugin` has no `BLOCK_CONTEXT_*` constants or `getSeq()` in 3.4/3.5 (those are 3.3-era).

## 5. Navigation menus

- `{load_menu}` → `smartyLoadNavigationMenuArea`: resolves the named **menu area** to the `NavigationMenu` assigned to it, renders `frontend/components/navigationMenu.tpl` (iterates `$navigationMenu->menuTree`, nested `<ul>/<li>`).
- Themes declare areas with `addMenuArea(['primary', 'user'])`; managers assign menus to areas in Website Settings → Setup → Navigation.
- Core NMI types (`NavigationMenuItem`, value = name): `NMI_TYPE_ABOUT`, `NMI_TYPE_SUBMISSIONS`, `NMI_TYPE_MASTHEAD`, `NMI_TYPE_CONTACT`, `NMI_TYPE_ANNOUNCEMENTS`, `NMI_TYPE_CUSTOM`, `NMI_TYPE_REMOTE_URL`, `NMI_TYPE_USER_*` (LOGOUT, LOGOUT_AS, PROFILE, DASHBOARD, REGISTER, LOGIN), `NMI_TYPE_ADMINISTRATION`, `NMI_TYPE_SEARCH`, `NMI_TYPE_PRIVACY`.
- Plugins add custom item types via hooks in `PKPNavigationMenuService`:
  ```php
  Hook::add('NavigationMenus::itemTypes', function ($hook, $args) {
      $types = &$args[0];
      $types['NMI_TYPE_MY_PAGE'] = ['title' => __('...'), 'description' => __('...')];
      return false;
  });
  // rendering/visibility: 'NavigationMenus::itemCustomTemplates' [&$templates]
  // and 'NavigationMenus::displaySettings' [$navigationMenuItem, $navigationMenu]
  ```

## 6. Galley URL patterns (for customizing galley buttons)

- List links (`objects/galley_link.tpl`) use **`op="view"`**: `{url page=$page op="view" path=$path}` where path = `[$bestArticleId, $bestGalleyId]` (article) or `[$bestIssueId, $bestGalleyId]` (issue); older versions: `[id, "version", publicationId, galleyId]`.
- Download op pattern: `article/download/{submissionId}/{galleyId}/{fileId}` (versioned: `article/download/{id}/version/{publicationId}/{galleyId}/{fileId}`).
- Always derive ids via `$galley->getBestGalleyId()` / `$article->getBestId()` / `$publication->getData('urlPath')` — these honor custom URL paths.

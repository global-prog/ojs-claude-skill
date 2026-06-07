# OJS Editorial Workflow & Journal Configuration (3.4 / 3.5)

Verified against Learning OJS (docs.pkp.sfu.ca/learning-ojs/ — default is now 3.5; 3.4 lives at `/learning-ojs/3.4/en/`), the Crossref manual, and OJS source locales.

## 1. Settings map

**Journal Settings**: Masthead (title, initials, abbreviation, publisher, ISSN, summary, editorial team, about) · Contact (principal + technical support) · Sections (policies, word limits, peer-review toggle, editor auto-assign, restrict-to-editors, inactive) · Categories.

**Website Settings**: Appearance (theme + theme options, logos, homepage image, footer, sidebar blocks, custom CSS, favicon) · Setup (Information pages, Languages/locales, Navigation menus, Announcements, Lists pagination, Privacy Statement, Date/Time) · Plugins (installed + gallery) · Static Pages (plugin).

**Workflow Settings**: Submission (disable toggle, metadata fields, components/file types, checklist, author guidelines) · Review (default mode, file-access restriction, one-click reviewer access, response/completion deadlines, automated reminders, guidance, competing interests, Review Forms; 3.5 adds "Suggest Reviewers" toggle) · Publisher Library · Emails (signature, templates editor).

**Distribution Settings**: License (copyright holder, CC license, copyright year basis) · **DOIs** (3.4+ core system — see §7) · Search Indexing (description, custom meta tags) · Payments (currency, PayPal/manual) · Access (OA / subscription / hybrid; OAI toggle) · Archiving (LOCKSS/CLOCKSS, PKP PN).

**Users & Roles**: users list, roles & stage assignments, site access options.

## 2. Roles & permission tiers

| Tier | Roles | Scope |
|---|---|---|
| Site Admin | — | whole installation |
| Managers | Journal Manager, Journal Editor, Production Editor | full workflow + all settings |
| Section Editors | Section Editor, Guest Editor | full workflow, **no settings** |
| Assistants | Copyeditor, Layout Editor, Proofreader, Designer, Indexer, … | only assigned stages |
| Reviewers | Reviewer | assigned reviews only |
| Authors | Author | submit + own submissions |
| Readers | Reader | public site |
| Subscription Managers | Subscription Manager | subscription settings |

Roles map to workflow stages via a stage-assignment matrix (editable; custom roles supported). Self-registration recommended only for Author/Reviewer. Numeric ROLE_ID values → `constants.md`.

## 3. Workflow stages & editorial decisions

**Submission** → Send to Review · Accept and Skip Review · Decline Submission · Change Decision. Section editors assigned via Participants; pre-review discussions.

**Review** → rounds-based. Decisions: Request Revisions (with/without new round) · Accept Submission · Decline · New Review Round · **Cancel Review Round** (3.4+) · Change Decision. Reviewer management: Add/Unassign/Cancel/Reinstate Reviewer, Email Reviewer, Read Review, Thank Reviewer. **Review Files** (sent to reviewers) vs **Revision Files** (author's revised versions). Recommend-only editors get "Make Recommendation" instead of decisions.

**Copyediting** → Draft Files worked on; final copyedited files to the Copyedited panel · Send to Production · Cancel Copyediting (back to review).

**Production** → create galleys; Schedule for Publication (assign to issue; requires Journal Editor authority — section editors cannot publish).

Decision/stage integer ids for the API → `constants.md`.

## 4. Review process

- Modes (per assignment; default in Workflow → Review): Anonymous Reviewer/Anonymous Author (double-anonymous) · Anonymous Reviewer/Disclosed Author · Open.
- Reviewer recommendations: Accept · Revisions Required · Resubmit for Review · Resubmit Elsewhere · Decline · See Comments.
- Reviewer flow: Request → Guidelines → Download & Review (comments for author+editor vs editor-only) → Upload files + recommendation.
- Custom Review Forms configurable per journal; deadlines (response + completion) with automated overdue reminders (require working scheduled tasks — see admin-operations.md §4).
- 3.5: authors can suggest reviewers at submission (toggle), stored as ReviewerSuggestion.

## 5. Publication, versioning, issues

- A Submission has one or more **Publication** versions; each publication has tabs: Title & Abstract, Contributors, Metadata, References, Galleys, Permissions & Disclosure, Issue, Identifiers (DOI).
- Galleys: PDF (most common), HTML, XML/JATS, ePub, media. **3.5 adds basic in-workflow JATS support** (dedicated JATS file stage 21 + preview). In 3.4 JATS is produced with external tools and uploaded.
- Publishing: assign to issue → Schedule for Publication; per-article date may differ from issue date. Issue lifecycle: Create (volume/number/year/title/cover) → add & order articles → preview → publish (optional notify readers) → can unpublish.
- **Versioning**: after publication, unpublish to fix or create a new version (`POST .../publications/{id}/version` via API); readers of old versions see a notice pointing to the latest; old versions stay accessible.
- **Continuous publication is NOT in 3.4/3.5** — it arrives in OJS 3.6 (with preprints/AO→VoR versioning). Workarounds today: rolling "current issue" or the third-party Forthcoming plugin.

## 6. Emails (Mailables system, 3.4+)

- Edit under Workflow → Emails → "Add and edit templates"; searchable, filterable by stage/sender/recipient; "Reset All" restores defaults.
- Architecture: a **Mailable** class (`PKP\mail\mailables\*`) declares its default template key; defaults ship in `emailTemplates.xml`; journals override per-context; extra templates attach to a mailable via `alternateTo`. Lookup in code: `Repo::emailTemplate()->getByKey($contextId, $key)`.
- The pre-3.4 `Mail`/`SubmissionMail` classes are gone; the `Mail::send` hook was removed in 3.5.

## 7. DOIs & Crossref (3.4+ core system)

The pre-3.4 DOI plugin is replaced by core DOI management:
- **Distribution → DOIs → Setup**: enable; choose objects (articles, issues, galleys); DOI prefix (`10.xxxx`); automatic assignment timing; suffix mode — Default (recommended auto 8-char), None (manual), or custom pattern.
- Custom suffix pattern tokens (verified): `%j` journal initials · `%v` volume · `%i` issue number · `%Y` year · `%a` article id · `%g` galley id · `%f` file id · `%p` page number · `%x` custom identifier. Legacy default patterns: issues `%j.v%vi%i`, articles `%j.v%vi%i.%a`, galleys `%j.v%vi%i.%a.g%g`. PKP marks custom patterns "not recommended".
- **Distribution → DOIs → Registration**: pick agency plugin (Crossref Manager, DataCite Manager; mEDRA), enter credentials (Crossref: depositor name/email, username/password), enable automatic deposit.
- **DOIs management page** (left nav): bulk assign/deposit/export, mark registered/stale; statuses (Unregistered/Submitted/Registered/Error/Stale → `constants.md`). Full REST endpoints under `/dois` (→ rest-api.md). Deposits run as queue jobs — if deposits hang, check jobs.
- 3.5: DOI search in the manager; Crossref plugin 5.4.0.

## 8. ORCID

- 3.3/3.4: separate ORCID Profile plugin (Plugin Gallery). Needs ORCID API credentials (Public or Member; sandbox/production).
- **3.5: ORCID is in core** — Settings include editor controls, ORCID in user invitations, authors/reviewers can connect iDs any time, publication updates pushed to ORCID. API endpoints `/orcid/*` (→ rest-api.md).

## 9. Statistics

- Article views/downloads (graph/table, monthly/daily), Editorial Activity (submissions received, days-to-decision, accept/decline rates; monthly report email), Users counts, optional geo/institutional stats.
- Report CSV exports: Articles, Review Report, Subscriptions, COUNTER.
- COUNTER R5 stats engine since 3.4 (usage processed via scheduled tasks + jobs); machine access via SUSHI API (→ rest-api.md §5). If stats stop updating: scheduled tasks/jobs are down.

## 10. Distribution integrations

- **Preservation**: PKP PN plugin (free dark archive; accept terms in plugin), LOCKSS/CLOCKSS under Distribution → Archiving.
- **Indexing**: Google Scholar works via embedded citation meta tags (Google Scholar plugin; needs clean metadata + valid HTTPS); OAI-PMH for harvesters; DOAJ application guide at docs.pkp.sfu.ca/doaj/.
- **Access models**: Open Access, Subscription (individual = user account; institutional = IP ranges/domain), Hybrid/delayed OA (auto-open after N months). Payments: APCs, reader fees via PayPal (auto-recorded) or manual.

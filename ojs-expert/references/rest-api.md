# OJS REST API, OAI-PMH & SUSHI (3.4.x / 3.5.x)

Verified against the OpenAPI sources in `pkp/ojs` (`docs/dev/swagger-source.json` on `stable-3_4_0` and `stable-3_5_0`) and PKP docs. Published HTML reference exists for 3.4 only: https://docs.pkp.sfu.ca/dev/api/ojs/3.4 (no 3.5 page — read the in-repo swagger source for 3.5). 3.4 = 110 operations; 3.5 = 118 (8 added, 0 removed).

## 1. Authentication

- **API token (JWT)**: user generates it under **User Profile → API Key**. Requires `api_key_secret` set in `config.inc.php` `[security]` (note: some docs typo it as `api_secret_key` — the real config key is `api_key_secret`). Pass on every request:
  ```
  Authorization: Bearer eyJ0e...
  ```
- The `apiToken` **query parameter is deprecated** since 3.4 — use the header.
- Cookie auth works for same-domain browser requests but needs a CSRF token on POST/PUT/DELETE. Token auth needs no CSRF.
- Apache may strip the `Authorization` header — fix with `CGIPassAuth On` (see pkp-lib issue #9320).
- Permissions follow the user's roles; admin-only endpoints need a site-admin token via the `_` site context.

## 2. Base URL forms

| Scenario | URL |
|---|---|
| `restful_urls = On` (mod_rewrite) | `https://host/<journalPath>/api/v1/...` |
| `restful_urls = Off` (default) | `https://host/index.php/<journalPath>/api/v1/...` |
| Site-level (admin) | `https://host/index.php/_/api/v1/...` (literal `_` context) |

(`disable_path_info` is a legacy ≤3.x-early setting and does not exist in 3.4/3.5.)

**Conventions:** pagination via `count` + `offset`; multilingual fields are locale-keyed objects `{"title":{"en":"..."}}` (in requests too); many objects include `_href`; errors return `{"error":"<key>","errorMessage":"<text>"}` with HTTP 400/403/404/409/413/500. No rate limiting is built in.

## 3. Endpoint inventory (3.5 superset; 🆕 = 3.5-only)

**Submissions**
- `GET /submissions` — filters: `assignedTo, categoryIds, count, daysInactive, isIncomplete, isOverdue, issueIds, offset, orderBy, orderDirection, searchPhrase, sectionIds, stageIds, status`
- `POST /submissions` · `GET|PUT|DELETE /submissions/{id}`
- `PUT /submissions/{id}/saveForLater` · `PUT /submissions/{id}/submit`
- 🆕 `GET /_submissions/assigned` · 🆕 `GET /_submissions/reviews` (`needsReviews, awaitingReviews, reviewsSubmitted, reviewsOverdue, revisionsRequested`) · 🆕 `GET /_submissions/viewsCount`

**Decisions**
- `GET /submissions/{id}/decisions` (3.5 adds filters `decisionTypes, editorIds, reviewRoundId, stageId`)
- `POST /submissions/{id}/decisions` — body `{"decision": <decisionTypeId>, ...}` (decision ids in constants.md)

**Submission files**
- `GET /submissions/{id}/files` (`fileStages, reviewRoundIds`) · `POST .../files`
- `GET|PUT|DELETE .../files/{fileId}` (`stageId`) · `PUT .../files/{fileId}/copy`

**Participants**: `GET /submissions/{id}/participants[/{stageId}]`

**Publications**
- `GET|POST /submissions/{id}/publications` · `GET|PUT|DELETE .../publications/{pubId}`
- `POST .../publications/{pubId}/version` (new version)
- `PUT .../publications/{pubId}/publish` · `PUT .../publications/{pubId}/unpublish`
- Contributors: `GET|POST .../publications/{pubId}/contributors`, `GET|PUT|DELETE .../contributors/{contributorId}`, `PUT .../contributors/saveOrder`

**Issues**: `GET /issues` (`isPublished, volumes, numbers, years, searchPhrase, count, offset, orderBy, orderDirection`) · `GET /issues/current` · `GET /issues/{issueId}`. **No issue create/edit via API** — that's UI-only.

**Users**
- `GET /users` (`roleIds, status, assignedToSubmission, assignedToSubmissionStage, assignedToSection, searchPhrase, count, offset, ...`) · `GET /users/{id}`
- `GET /users/reviewers` (`status, reviewerRating, reviewStage, reviewsCompleted, reviewsActive, daysSinceLastAssignment, averageCompletion, ...`)
- `PUT /users/{id}/endRole/{userGroupId}` (3.5 / late 3.4.x)

**Contexts (journals)**: `GET|POST /contexts` · `GET|PUT|DELETE /contexts/{id}` · `GET|PUT /contexts/{id}/theme` · `PUT /contexts/editDoiRegistrationAgencyPlugin`

**Site**: `GET|PUT /site` · `GET|PUT /site/theme` (use `_` context)

**Announcements**: `GET|POST /announcements` · `GET|PUT|DELETE /announcements/{id}` (`typeIds, searchPhrase`)

**DOIs** (added 3.4; manager/admin only)
- `GET /dois` (`status, count, offset`) · `POST /dois` · `GET|PUT|DELETE /dois/{doiId}` · `PUT /dois/depositAll` · `GET /dois/exports/{fileId}`
- Submissions: `POST /dois/submissions/assignDois`; `PUT /dois/submissions/{export|deposit|markRegistered|markUnregistered|markStale}`
- Issues: same verbs under `/dois/issues/...`

**Email templates**: `GET|POST /emailTemplates` (`alternateTo, isModified, searchPhrase`) · `GET|PUT|DELETE /emailTemplates/{key}` · `DELETE /emailTemplates/restoreDefaults`

🆕 **Emails**: `GET /emails/authorEmails` (`submissionId, eventType`) · `GET /emails/{emailId}`

🆕 **ORCID**: `POST /orcid/requestAuthorVerification/{authorId}` · `DELETE /orcid/deleteForAuthor/{authorId}`

**Institutions** (3.4+): `GET|POST /institutions` · `GET|PUT|DELETE /institutions/{id}`

**Mailables** (3.4+): `GET /mailables` (`searchPhrase`) · `GET /mailables/{id}`

**Vocabs**: `GET /vocabs` (`vocab, locale`) — controlled vocabularies (keywords, subjects, …)

**Temporary files**: `POST /temporaryFiles` (multipart `file`) → `{"id": N}`; reference as `temporaryFileId` in subsequent writes (logos, galley files). Only the uploading user can reference it. 413 = upload too large.

**Stats**
- `GET /stats/editorial` (`dateStart, dateEnd, sectionIds`) · `GET /stats/editorial/averages`
- `GET /stats/contexts[...]`, `GET /stats/issues[...]` (+ `/timeline`, `/{id}`, `/{id}/timeline`)
- `GET /stats/publications` (+ `/timeline`, `/{submissionId}`, `/{submissionId}/timeline`, `/files`, `/countries`, `/regions`, `/cities`)
- `GET /stats/users` (`registeredAfter, registeredBefore, status`)

**Backend/private** (discouraged for third parties): `GET /_submissions`, `PUT /_payments`, `POST /_uploadPublicFile`.

## 4. Worked examples (curl)

```bash
B="https://example.com/index.php/myjournal/api/v1"; A="Authorization: Bearer $TOKEN"

# Active submissions in external review (stage/status ids → constants.md)
curl -s -H "$A" "$B/submissions?stageIds=3&status=1&count=20&offset=0"

# Submission + its publications
curl -s -H "$A" "$B/submissions/219"
curl -s -H "$A" "$B/submissions/219/publications"

# Edit publication metadata (locale-keyed!)
curl -s -X PUT -H "$A" -H "Content-Type: application/json" \
  -d '{"title":{"en":"Revised title"},"abstract":{"en":"<p>New abstract</p>"}}' \
  "$B/submissions/219/publications/305"

# Version + publish
curl -s -X POST -H "$A" "$B/submissions/219/publications/305/version"
curl -s -X PUT  -H "$A" "$B/submissions/219/publications/306/publish"

# Two-step file upload (e.g. journal logo)
curl -s -X POST -H "$A" -F "file=@logo.png" "$B/temporaryFiles"        # -> {"id":123}
curl -s -X PUT -H "$A" -H "Content-Type: application/json" \
  -d '{"pageHeaderLogoImage":{"temporaryFileId":123,"altText":"Logo"}}' "$B/contexts/1"
```

The bundled `scripts/ojs_api.py` wraps all of this (auth header, pagination, JSON pretty-print, multipart upload).

## 5. COUNTER R5 SUSHI API

Base: `/api/v1/stats/sushi/` (both 3.4 and 3.5 — COUNTER R5, not 4.1):

```
GET status | members | reports
GET reports/pr      # Platform Master Report        (pkp-lib)
GET reports/pr_p1   # Platform Usage standard view  (pkp-lib)
GET reports/tr      # Title Master Report           (OJS)
GET reports/tr_j3   # Journal Usage by Access Type  (OJS)
GET reports/ir      # Item Master Report            (OJS)
GET reports/ir_a1   # Journal Article Requests      (OJS)
```

Public by default (site setting `isSushiApiPublic`); when private, requires site-admin/manager auth. `members` requires `customer_id`. Report params: `begin_date`/`end_date` (`YYYY-MM[-DD]`), `item_id`, `yop`, `metric_type` (required for PR/TR/IR).

## 6. OAI-PMH

- Endpoint: `https://host/index.php/<journalPath>/oai` (plus a site-wide `/index.php/oai`).
- Standard verbs: `Identify`, `ListMetadataFormats`, `ListSets`, `ListIdentifiers`, `ListRecords`, `GetRecord`.
- Formats (plugin-dependent): `oai_dc` (always), JATS (`oaiJats` plugin), `marcxml`, `marc`, `rfc1807`. Confirm exact prefixes per install via `ListMetadataFormats`.
- Config (`config.inc.php`): `oai = On`, `repository_id` (part of record identifiers), `oai_max_records = 100`.
- Example: `.../oai?verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:<repository_id>:article/219`

## 7. API changes between versions

- **3.3 → 3.4**: +48 operations. Added DOIs, Institutions, Mailables, Decisions, Contributors, Stats contexts/issues/users; `saveForLater`/`submit`; file `copy`; email templates keyed by `{key}` + `restoreDefaults`; stats/publications restructured (removed `/abstract`, `/galley` → `/timeline`, `/files`, geo). `apiToken` param deprecated. `submissionProgress` became a string.
- **3.4 → 3.5**: +8 operations (Emails, ORCID, dashboard `_submissions/*`, `endRole`), decision-list filters. **Internally** the API moved Slim → Laravel routing (affects plugin API code, not consumers). No endpoints removed.

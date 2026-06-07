# OJS/PKP Verified Integer Constants (3.4.0 / 3.5.0)

All values read directly from `pkp/pkp-lib` (and `pkp/ojs`) source on branches `stable-3_4_0` and `stable-3_5_0`. Identical in both branches unless noted. Use these for REST API query params (`stageIds`, `status`, `roleIds`, `fileStages`, `decision`...) and in PHP code via the class constants — never hardcode unverified integers.

## Roles — `PKP\security\Role` (`classes/security/Role.php`)

| Constant | Value |
|---|---|
| ROLE_ID_SITE_ADMIN | 1 |
| ROLE_ID_MANAGER | 16 |
| ROLE_ID_SUB_EDITOR | 17 |
| ROLE_ID_ASSISTANT | 4097 |
| ROLE_ID_REVIEWER | 4096 |
| ROLE_ID_AUTHOR | 65536 |
| ROLE_ID_READER | 1048576 |
| ROLE_ID_SUBSCRIPTION_MANAGER | 2097152 |

## Workflow stages — global defines in `classes/core/PKPApplication.php`

| Constant | Value |
|---|---|
| WORKFLOW_STAGE_ID_PUBLISHED | 0 |
| WORKFLOW_STAGE_ID_SUBMISSION | 1 |
| WORKFLOW_STAGE_ID_INTERNAL_REVIEW | 2 (OMP; unused in OJS) |
| WORKFLOW_STAGE_ID_EXTERNAL_REVIEW | 3 |
| WORKFLOW_STAGE_ID_EDITING | 4 (copyediting) |
| WORKFLOW_STAGE_ID_PRODUCTION | 5 |

## Submission status — `PKP\submission\PKPSubmission`

| Constant | Value |
|---|---|
| STATUS_QUEUED | 1 (active/in workflow) |
| STATUS_PUBLISHED | 3 |
| STATUS_DECLINED | 4 |
| STATUS_SCHEDULED | 5 |

(No value 2. Publications use these same STATUS_* values — `PKPPublication` defines no own status integers.)

## Submission file stages — `PKP\submissionFile\SubmissionFile`

| Constant | Value |
|---|---|
| SUBMISSION_FILE_SUBMISSION | 2 |
| SUBMISSION_FILE_NOTE | 3 |
| SUBMISSION_FILE_REVIEW_FILE | 4 |
| SUBMISSION_FILE_REVIEW_ATTACHMENT | 5 |
| SUBMISSION_FILE_FINAL | 6 |
| SUBMISSION_FILE_COPYEDIT | 9 |
| SUBMISSION_FILE_PROOF | 10 |
| SUBMISSION_FILE_PRODUCTION_READY | 11 |
| SUBMISSION_FILE_ATTACHMENT | 13 |
| SUBMISSION_FILE_REVIEW_REVISION | 15 |
| SUBMISSION_FILE_DEPENDENT | 17 |
| SUBMISSION_FILE_QUERY | 18 |
| SUBMISSION_FILE_INTERNAL_REVIEW_FILE | 19 |
| SUBMISSION_FILE_INTERNAL_REVIEW_REVISION | 20 |
| SUBMISSION_FILE_JATS | 21 — **3.5 only** |

3.5 also adds grouping arrays `INTERNAL_REVIEW_STAGES = [19, 20]`, `EXTERNAL_REVIEW_STAGES = [4, 15]`. Values 1, 7, 8, 12, 14, 16 are unused/legacy.

## Editorial decisions — `PKP\decision\Decision` (full set identical 3.4/3.5)

| Constant | Value | | Constant | Value |
|---|---|---|---|---|
| INTERNAL_REVIEW | 1 | | SKIP_EXTERNAL_REVIEW | 17 |
| ACCEPT | 2 | | SKIP_INTERNAL_REVIEW | 18 |
| EXTERNAL_REVIEW | 3 | | ACCEPT_INTERNAL | 19 |
| PENDING_REVISIONS | 4 | | PENDING_REVISIONS_INTERNAL | 20 |
| RESUBMIT | 5 | | RESUBMIT_INTERNAL | 21 |
| DECLINE | 6 | | DECLINE_INTERNAL | 22 |
| SEND_TO_PRODUCTION | 7 | | RECOMMEND_ACCEPT_INTERNAL | 23 |
| INITIAL_DECLINE | 8 | | RECOMMEND_PENDING_REVISIONS_INTERNAL | 24 |
| RECOMMEND_ACCEPT | 9 | | RECOMMEND_RESUBMIT_INTERNAL | 25 |
| RECOMMEND_PENDING_REVISIONS | 10 | | RECOMMEND_DECLINE_INTERNAL | 26 |
| RECOMMEND_RESUBMIT | 11 | | REVERT_INTERNAL_DECLINE | 27 |
| RECOMMEND_DECLINE | 12 | | NEW_INTERNAL_ROUND | 28 |
| RECOMMEND_EXTERNAL_REVIEW | 13 | | BACK_FROM_PRODUCTION | 29 |
| NEW_EXTERNAL_ROUND | 14 | | BACK_FROM_COPYEDITING | 30 |
| REVERT_DECLINE | 15 | | CANCEL_REVIEW_ROUND | 31 |
| REVERT_INITIAL_DECLINE | 16 | | CANCEL_INTERNAL_REVIEW_ROUND | 32 |

(`*_INTERNAL` values apply to OMP/internal review; OJS uses the external-review set.)

## Review assignments — `PKP\submission\reviewAssignment\ReviewAssignment`

Review method: ANONYMOUS = 1 · DOUBLEANONYMOUS = 2 · OPEN = 3

Reviewer recommendation (`SUBMISSION_REVIEWER_RECOMMENDATION_*`, still present in 3.5):
ACCEPT = 1 · PENDING_REVISIONS = 2 · RESUBMIT_HERE = 3 · RESUBMIT_ELSEWHERE = 4 · DECLINE = 5 · SEE_COMMENTS = 6

Reviewer rating: VERY_GOOD = 5 · GOOD = 4 · AVERAGE = 3 · POOR = 2 · VERY_POOR = 1

Status (`REVIEW_ASSIGNMENT_STATUS_*`): AWAITING_RESPONSE = 0 · DECLINED = 1 · RESPONSE_OVERDUE = 4 · ACCEPTED = 5 · REVIEW_OVERDUE = 6 · RECEIVED = 7 · COMPLETE = 8 · THANKED = 9 · CANCELLED = 10 · REQUEST_RESEND = 11 · VIEWED = 12 (2 and 3 are skipped)

Considered flags: NEW = 0 · UNCONSIDERED = 1 · RECONSIDERED = 2 · CONSIDERED = 3 · VIEWED = 4 (**VIEWED is 3.5-only**)

Note: 3.5 adds `ReviewerSuggestion` (`classes/submission/reviewer/suggestion/`) for author-suggested reviewers — a separate concept; recommendation constants did NOT move.

## Issue access — `APP\issue\Issue` (pkp/ojs)

ISSUE_ACCESS_OPEN = 1 · ISSUE_ACCESS_SUBSCRIPTION = 2

## DOI status — `PKP\doi\Doi`

STATUS_UNREGISTERED = 1 · STATUS_SUBMITTED = 2 · STATUS_REGISTERED = 3 · STATUS_ERROR = 4 · STATUS_STALE = 5

## Quick API recipes using these values

```
# All published articles:                GET /submissions?status=3
# Active subs in copyediting:            GET /submissions?status=1&stageIds=4
# All journal managers:                  GET /users?roleIds=16
# Authors named smith:                   GET /users?roleIds=65536&searchPhrase=smith
# Unregistered DOIs:                     GET /dois?status=1
# Review files of a submission:          GET /submissions/{id}/files?fileStages=4
# Record an Accept decision:             POST /submissions/{id}/decisions {"decision":2,...}
```

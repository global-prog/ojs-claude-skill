# OJS Administration: Install, Configure, Upgrade, Operate (3.4.x / 3.5.x)

Verified against the PKP Admin Guide, Upgrade Guide, release notebooks, and `config.TEMPLATE.inc.php` on `stable-3_4_0` / `stable-3_5_0`.

## 1. System requirements

| | OJS 3.4 | OJS 3.5 |
|---|---|---|
| PHP | **8.0+** | **8.2.0+** |
| PHP extensions | mbstring, xml, intl | php-mbstring, php-xml, php-intl |
| MySQL | 5.7.22+ | 5.7.22+ (MariaDB 10.x equivalent) |
| PostgreSQL | 9.5+ | 9.5+ |
| DB driver values | only `mysqli` / `postgres9` | same |

(3.3 LTS: PHP 7.3+.) UTF-8 is mandatory since 3.4.

## 2. Installation

1. Extract tarball: `tar -xvf ojs-3.5.0-4.tar.gz` into the web root.
2. Create `files_dir` **outside the web root** (e.g. `/var/www/files`) — must not be web-accessible.
3. Make writable by the web server user: `config.inc.php` (optional), `public/`, `cache/` (incl. `t_cache`, `t_config`, `t_compile`, `_db`), and the `files_dir`. Community-canonical scheme on a dedicated host: `chown -R <user>:www-data`, dirs `750` (web-writable dirs owned/writable by the web user).
4. Run the web installer (browse to the site) — creates admin account; or CLI: `php tools/install.php`.
5. Post-install: set `api_key_secret`, `allowed_hosts`, `force_ssl`, captcha in `config.inc.php`; configure jobs + scheduler (§4).

## 3. config.inc.php — settings that matter

**[general]**
- `installed`, `base_url`
- `app_key` — **3.5 only** (Laravel APP_KEY; generated at install/upgrade; if missing: `php lib/pkp/tools/appKey.php`)
- `session_cookie_name = OJSSID`, `session_lifetime = 30`, `session_samesite = Lax`
- `time_zone = "UTC"` — required since 3.4
- `allowed_hosts` — 3.4+; JSON array of hostnames, set it in production (HOST-header injection guard)
- `trust_x_forwarded_for = Off` — only enable behind a trusted proxy
- `restful_urls = Off` — On needs mod_rewrite; decides whether URLs (and API) need `index.php/`
- `scheduled_tasks` — **3.4 only**; removed in 3.5 (replaced by `[schedule]`)

**[database]** `driver` (`mysqli`/`postgres9`), `host`, `username`, `password`, `name`

**[security]**
- `salt` — long random value, never share
- `api_key_secret` — required for API tokens
- `encryption = sha1` (leave as is), `force_ssl`, `force_login_ssl`, `session_check_ip = On`
- `allowed_html`, `allow_plugin_install`
- 3.5 adds `cipher` / `cookie_encryption` (Laravel session/cookie layer)

**[files]** `files_dir` (outside webroot!), `public_files_dir = public`, `public_user_dir_size = 5000`, `umask = 0022`

**[email]** (Laravel/Symfony Mailer since 3.4 — PHPMailer gone)
`default = sendmail|smtp|log|phpmailer`, `sendmail_path`, `smtp_server/port/auth/username/password`, `allow_envelope_sender`, `force_default_envelope_sender`, `require_validation`, `validation_timeout`

**[schedule]** — **3.5 only**: `task_runner = On`, `task_runner_interval = 60`, `scheduled_tasks_report_error_only = On`

**[queues]**: `job_runner = On`, `job_runner_max_jobs = 30`, `job_runner_max_execution_time = 30`, `job_runner_max_memory = 80`, `delete_failed_jobs_after = 180`, `process_jobs_at_task_scheduler` (**3.5 only**)

**[cache]** 3.4: `object_cache`; 3.5: `default` driver (`opcache`/`file`). `web_cache`, `web_cache_hours`.

**[i18n]** `locale = en` (short codes since 3.4), `connection_charset = utf8`

**[search]** `min_word_length = 3`, `results_per_keyword = 500`, optional `index[<mime>]` external text extractors (pdftotext etc.). Built-in SQL search only — no core Solr/Elasticsearch config.

**[oai]** `oai = On`, `repository_id`, `oai_max_records = 100`

**[captcha]** ReCaptcha (`recaptcha`, keys, `captcha_on_register`, `captcha_on_login`) and — 3.5 — **ALTCHA** (`altcha`, `altcha_hmackey`, per-form toggles)

**[debug]** `show_stacktrace`, `display_errors`, `deprecation_warnings` — all Off in production

## 4. Background jobs & scheduled tasks (two separate subsystems!)

### Jobs/queues (3.4+; emails, stats, DOI deposits, search indexing)
Laravel queues, database driver, single `default` queue. Pick ONE run mode:
1. **Built-in runner** (default): `job_runner = On` — jobs piggyback on web requests. Fine for small sites.
2. **Worker daemon** (recommended): `job_runner = Off` + Supervisor running `php lib/pkp/tools/jobs.php work`. After deploys: `php lib/pkp/tools/jobs.php restart`.
3. **Cron**: `job_runner = Off` + every minute `php lib/pkp/tools/jobs.php run [--once]`.

Inspect: `php lib/pkp/tools/jobs.php list` / `failed`, or UI Administration → Jobs / Failed Jobs.

### Scheduled tasks (reminders, usage-stats processing, expirations)
- **3.4**: Acron plugin (XML task lists) and/or `scheduled_tasks` config + `tools/runScheduledTasks.php` cron.
- **3.5**: **Laravel Task Scheduler — Acron removed.** Either `task_runner = On` (built-in) or cron:
  `* * * * * php lib/pkp/tools/scheduler.php run >> /dev/null 2>&1`
  Commands: `scheduler.php list | run | test`. Logs: `<files_dir>/scheduledTaskLogs/`.

## 5. Upgrading

Supported entry path: 3.2.1-x can upgrade to any 3.3+; upgrade old installs through 3.3 first. Check the release's `docs/UPGRADE` for per-version minimums. 3.4→3.5 requires PHP 8.2 first.

Procedure (condensed from the official 15-step tutorial):
```bash
# 1. Stop background tasks (kill workers SIGTERM, disable cron/Acron); block site access
# 2. BACKUP everything
mysqldump --host=$DB_HOST -u $DB_USER -p$DB_PASS $DB_NAME --result-file=backupDB-$DATE.sql
tar czf private-$DATE.tgz $FILES_DIR
tar czf public-$DATE.tgz $WEB_PATH/public
cp $WEB_PATH/config.inc.php backup/
# 3. Swap code (keep old tree as backup)
mv $WEB_PATH $BACKUP_PATH/old-code
mkdir $WEB_PATH && tar --strip-components=1 -xzf ojs-3.5.0-4.tar.gz -C $WEB_PATH
# 4. Restore config + public; diff config against new config.TEMPLATE.inc.php and merge
cp $BACKUP_PATH/old-code/config.inc.php $WEB_PATH/
cp -r $BACKUP_PATH/old-code/public/* $WEB_PATH/public/
# 5. Reinstall compatible versions of custom/third-party plugins into plugins/
# 6. Run the upgrade
cd $WEB_PATH
php tools/upgrade.php check
php -d memory_limit=2048M tools/upgrade.php upgrade | tee -a upgrade.log
# 7. Test, re-enable access and background tasks
```

Config-merge gotchas 3.4→3.5: new `app_key` (auto-added, else `appKey.php`), new `[schedule]` section, `scheduled_tasks` removed, `process_jobs_at_task_scheduler`, ALTCHA section. 3.3→3.4: `time_zone`, `allowed_hosts`, locale short codes, `[queues]`.

Common failures: memory exhaustion (raise `memory_limit`), wrong file ownership after code swap, locale mismatch after `en_US`→`en`, jobs/workers running during upgrade, third-party plugins built for the old version (remove them, upgrade, reinstall updated builds).

## 6. CLI tools inventory

`tools/` (OJS): `install.php`, `upgrade.php` (check/upgrade), `importExport.php`, `mergeUsers.php`, `rebuildSearchIndex.php`, `deleteSubmissions.php`, `cleanReviewerInterests.php`, `resolveAgencyDuplicates.php`

`lib/pkp/tools/`: `jobs.php` (work/run/list/failed/restart), `scheduler.php` (3.5: list/run/test), `appKey.php` (3.5), `installPluginVersion.php`, `installEmailTemplate.php`, `getHooks.php`, `migration.php`, `parseCitations.php`, `reprocessUsageStatsMonth.php`, locale tools

### importExport.php (verified argument order)
```bash
php tools/importExport.php list
php tools/importExport.php NativeImportExportPlugin usage
# Native XML (issues/articles); options before command: --no-embed, --use-file-urls
php tools/importExport.php NativeImportExportPlugin import <file.xml> <journal_path> <username>
php tools/importExport.php NativeImportExportPlugin export <file.xml> <journal_path> {issue|issues|article|articles} [id ...]
# Users XML
php tools/importExport.php UserImportExportPlugin import <file.xml> <journal_path>
php tools/importExport.php UserImportExportPlugin export <file.xml> <journal_path> [username ...]
```
Use CLI (not the UI) for large XML files with embedded binaries.

## 7. Security hardening checklist

1. Long random `salt` and `api_key_secret`; keep `encryption = sha1`.
2. `files_dir` outside the web root and not web-served.
3. Set `allowed_hosts`; `force_ssl = On` (valid cert — test with ssllabs); `session_check_ip = On`.
4. Tight file permissions: app files read-only to web server where possible; web-writable only `files_dir`, `cache/`, `public/`.
5. Enable captcha on registration/login (ReCaptcha, or ALTCHA in 3.5); `require_validation = On` against spam accounts.
6. Dedicated DB per install; automated backups (DB + files_dir): 7 daily / 4 weekly / 12 monthly.
7. `display_errors`/`show_stacktrace` Off in production; keep the install patched (security fixes ship as point releases, e.g. 3.3.0-22 / 3.4.0-10); watch PKP Announcements forum + `github.com/pkp/ojs/security`.
8. Antivirus-scan uploads at the server level; scrutinize unusual submissions (spam-injection vector).

## 8. Troubleshooting

- **Logs**: web-server error log (primary), `<files_dir>/scheduledTaskLogs/`, failed jobs (`jobs.php failed`).
- **White screen / 500**: usually file permissions (`files_dir`, `cache/`, `public/`) or PHP version mismatch. Temporarily set `[debug] show_stacktrace = On` / `display_errors = On` (revert!).
- **Emails not sending / stats not processing / DOIs not depositing**: check jobs (§4) — usually no worker is running, or all attempts failed (see Failed Jobs).
- **Reminders/automated emails not firing**: scheduled tasks not running (§4).
- **API 404s on /api/v1**: URL form mismatch — include `index.php/` when `restful_urls = Off`; Apache stripping `Authorization` header → `CGIPassAuth On`.
- **Garbled characters after upgrade**: DB charset vs `connection_charset` mismatch; verify `SHOW VARIABLES LIKE 'char%';` — everything UTF-8.
- **Stale UI after changes**: clear `cache/t_compile/`, `cache/t_cache/`, `cache/_db/` or use Administration → Expire Sessions / Clear Caches.
- **Plugin fatal after upgrade**: plugin built for old OJS — remove its directory, clear caches, reinstall a compatible release.

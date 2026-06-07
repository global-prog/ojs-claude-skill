# ojs-claude-skill — OJS Expert Skill for Claude

A comprehensive, source-verified [Claude Code](https://claude.com/claude-code) **Agent Skill** for [OJS (Open Journal Systems)](https://pkp.sfu.ca/software/ojs/) by PKP — covering plugin & theme development, REST API integration, system administration, and editorial workflow configuration for **OJS 3.4.x / 3.5.x** (with 3.3 differences noted).

Built and maintained by **[AL-NAKIB LTD](https://alnakib.com)**.

## What it does

Drop this skill into Claude Code and Claude becomes an OJS specialist that:

- **Develops plugins** — all 10 plugin categories with verified base-class APIs, the complete hooks catalog (arguments verified at call sites), settings UI for both 3.4 (Smarty/AjaxModal) and 3.5 (PluginSettingsController + Vue FormModal), migrations, scheduled tasks (post-Acron `HasTaskScheduler`), queue jobs, custom editorial decisions
- **Builds themes** — full `ThemePlugin` API, LESS variables, child themes, template-override hierarchy
- **Drives the REST API** — all 118 endpoints (verified from the OpenAPI sources), JWT auth, COUNTER R5 SUSHI, OAI-PMH, plus a bundled stdlib-only Python client
- **Administers installs** — `config.inc.php` reference, jobs vs. scheduler (the big 3.4↔3.5 trap), upgrade procedure, CLI tools, security hardening, troubleshooting
- **Configures journals** — workflow stages & decisions, roles, review process, DOIs/Crossref, ORCID, statistics
- **Never hallucinates magic numbers** — every integer constant (roles, stages, statuses, file stages, all 32 decision types…) extracted from real `pkp-lib` source

All reference material was verified against official PKP documentation (docs.pkp.sfu.ca) and the `pkp/ojs` + `pkp/pkp-lib` source on branches `stable-3_4_0` / `stable-3_5_0`.

## Installation

### Claude Code (personal skills)

```bash
git clone https://github.com/OWNER/ojs-claude-skill.git
# Windows
xcopy /E /I ojs-claude-skill\ojs-expert "%USERPROFILE%\.claude\skills\ojs-expert"
# macOS / Linux
cp -r ojs-claude-skill/ojs-expert ~/.claude/skills/ojs-expert
```

### Project-level (share with a team via the repo)

Copy `ojs-expert/` into your project's `.claude/skills/` directory.

Then just talk to Claude about anything OJS — the skill auto-triggers on mentions of OJS, PKP, pkp-lib, `config.inc.php`, plugin/theme work, etc.

## Structure

```
ojs-expert/
├── SKILL.md                          # router + core conventions + live-install safety rules
├── references/
│   ├── plugin-development.md         # anatomy, categories, lifecycle API, migrations, jobs, 3.5 migration checklist
│   ├── hooks-catalog.md              # ~50 hooks verified at call sites: args, ABORT semantics, removed-in-3.5
│   ├── ui-forms-handlers.md          # Field* classes, FormComponent, handlers, authorization policies
│   ├── theme-development.md          # ThemePlugin API, LESS, child themes, template hierarchy
│   ├── rest-api.md                   # full endpoint inventory, auth, SUSHI, OAI-PMH, curl recipes
│   ├── constants.md                  # verified integer constants (roles, stages, statuses, decisions…)
│   ├── admin-operations.md           # install, config.inc.php, upgrade, jobs/scheduler, hardening
│   ├── editorial-workflow.md         # settings map, roles, decisions, review, DOI/Crossref, ORCID
│   ├── architecture.md               # Repo pattern, schemas, routers, directory layout
│   └── versions.md                   # release lines, LTS status, per-version diff matrix, docs map
└── scripts/
    └── ojs_api.py                    # stdlib-only OJS REST API client (auth, pagination, upload)
```

## Quick API client example

```bash
python ojs-expert/scripts/ojs_api.py \
  --base "https://journal.example.com/index.php/myjournal" \
  --token "$OJS_API_TOKEN" \
  GET submissions -p status=1 -p count=20
```

## Version targeting

| OJS line | Status (June 2026) | Skill coverage |
|---|---|---|
| 3.3.0-x | Current LTS | differences noted |
| 3.4.0-x | Stable | full |
| 3.5.0-x | Current / next LTS | full |
| 3.6 | Unreleased | roadmap notes only |

## License

MIT © 2026 [AL-NAKIB LTD](https://alnakib.com). OJS and PKP are trademarks of their respective owners; this project is not affiliated with or endorsed by PKP.

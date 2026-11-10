# Codex++ model catalog mechanics

Observed on Codex++ 1.6.0 (Windows), corrected on 2026-11-04 using the installed
state and the upstream v1.6.0 generator source. Earlier sidecar guidance was
incorrect. Re-check behavior after changing application versions.

## Where the files live

| Purpose | Path |
| --- | --- |
| Codex++ settings (source of truth) | `%USERPROFILE%\.codex-session-delete\settings.json` |
| Codex++ log | `%USERPROFILE%\.codex-session-delete\codex-plus.log` |
| Generated catalogs | `%USERPROFILE%\.codex\model-catalogs\<relay-id>.json` |
| Config the app actually reads | `%USERPROFILE%\.codex\config.toml` |
| Auth written alongside config | `%USERPROFILE%\.codex\auth.json` |

`settings.json` holds roughly 66 top-level keys. The relevant ones:

- `activeRelayId` picks the profile in use.
- `relayProfiles[]` stores one object per provider.
- `relayCommonConfigContents` is shared TOML prepended to every profile.
- `relayContextConfigContents` holds MCP servers and plugin toggles.

Each relay profile carries `id`, `name`, `configContents`, `modelList`,
`modelWindows`, `modelAutoCompact`, `modelMetadata`, `modelInsertMode`, and
credentials. `configContents` is a TOML string; `modelMetadata` is a JSON string
that is usually `""`.

## How config.toml is produced

Codex++ concatenates `relayCommonConfigContents` with the profile's
`configContents` and writes the result to `config.toml`. A line-by-line
comparison of the two sides matches exactly apart from a handful of
environment-specific entries that the launcher substitutes.

Consequence: editing `config.toml` in isolation only appears to work. Any
provider switch or restart rebuilds it from the profile text.

## How the catalog is produced

At startup the app derives a catalog path as
`model-catalogs/<profile-id>.json` and writes a catalog built from templates
compiled into the executable. Templates ship for known model families
(`gpt-5.6`, `gpt-6`, DeepSeek, GLM, Qwen, Kimi, MiniMax, and others).

A model that matches no template receives a generic entry:

- `display_name` equals the slug
- `default_reasoning_level` is `medium`
- `supported_reasoning_levels` is exactly `low/medium/high/xhigh`
- `context_window` falls back to 272000

That generic entry is indistinguishable in the picker from a model that genuinely
supports only four levels, which is why the tier list looks authoritative when it
is not.

## Native Overrides Versus UI Metadata

The profile's `modelMetadata` is a JSON string containing a map from exact model
slugs to native catalog overrides. In `crates/codex-plus-core/src/relay_config.rs`,
`parse_model_metadata_map` parses it and `apply_model_metadata_overrides` merges
each entry into the generated catalog.

The required fields are `supported_reasoning_levels` (items with `effort`) and
`default_reasoning_level`. `supportedReasoningEfforts` (items with
`reasoningEffort`) and `defaultReasoningEffort` belong to the renderer response
schema. The generator copies unknown fields, so writing only UI fields leaves
the original native four-tier list unchanged. There is no validation error,
which made earlier attempts appear successful.

The `/codex-model-catalog` UI route separately returns built-in UI metadata and
does not itself trigger regeneration. Persisting a native override and calling
only that read route does not reload the running Codex process.

The renderer's own tier helper does inject `max` and `ultra` for matching names,
but only when `codexPlusModelMetadata(name)` resolves. No entry means no
injection, and the four-tier fallback stands.

## Why the Sidecar Workaround Fails

The generated filename is `<profile-id>.json`, but
`is_codex_plus_managed_model_catalog` checks the directory, not the basename.
Any relative path beginning with `model-catalogs/`, or absolute path containing
`/model-catalogs/`, is considered managed.

`apply_model_catalog_to_config` replaces a managed pointer with the active
profile's canonical path. A `-tiers.json` file can survive physically while no
longer being referenced. The manager then backfills profile text from the live
config, propagating the canonical pointer into settings.

The 2026-11-04 log showed `manager.backfill_relay_profile_from_live` followed by
`manager.switch_relay_profile`, matching the observed loss of the sidecar
pointer. Editing `config.toml` again only postpones the next overwrite.

## Durable Fix

Persist native overrides in every relay profile. Regeneration then reapplies
the desired tiers instead of discarding them. Existing model IDs, lists,
context windows, authentication, and provider URLs are not changed.

The user script at
`%APPDATA%\Codex++\user_scripts\00-max-tier-policy.js` loads through Codex++'s
normal user-script lifecycle. It ensures the two requested overrides across
existing and future profiles, translates the target models' UI responses, and
preserves the latest bridge on cleanup or reconnection. It registers no polling
timer. Only already-listed models receive a UI descriptor. An existing valid
native default is preserved; `max` is the fallback, not a forced replacement
for every existing default.

The policy's `sync()` persists metadata, not generated catalog files. New
profiles are repaired on settings reads, and supplied profile arrays are
normalized on settings writes. If first catalog generation precedes repair,
the UI overlay can expose MAX before the native Codex process has loaded it.
Regeneration and a real restart are still required to verify that native load.

Settings and script backups from the repair are kept under
`~/.codex-session-delete/backups/reasoning-max-20261104-200611/`.

## Live bridge

The launcher starts the desktop app with `--debug-port <port>` and
`--helper-port <port>`. The CDP target list at
`http://127.0.0.1:<port>/json/list` contains a page target whose URL starts with
`app://`. The injected renderer script exposes:

```js
window.__codexSessionDeleteBridge(route, payload) // -> Promise
```

Routes that matter here:

- `/settings/get` returns the whole settings object.
- `/settings/set` accepts a partial settings object and persists it.
- `/codex-model-catalog` returns the catalog currently on disk.
- `/user-scripts/reload` reloads installed scripts through their cleanup lifecycle.

Mutating through `/settings/set` is safe while the app runs, because the app
holds settings in memory and would otherwise overwrite an externally edited
`settings.json`.

`window.codexPlus.call(...)` is an extension API and rejects internal routes such
as `/codex-model-catalog` with `未开放的路由`. Use the bridge directly.

## Deployment Bridge Recipe

Run from the skill root in PowerShell, only after backing up and installing the
tested script. The bundled `scripts/cdp.py` provides `CdpSession`; no browser
automation package is needed. This call mutates settings if rules are missing.
It prints only policy state and counts, never complete settings.

```powershell
@'
import json
from scripts.cdp import CdpSession

session = CdpSession()
try:
    reloaded = session.bridge("/user-scripts/reload", {})
    if isinstance(reloaded, dict) and (
        reloaded.get("status") == "failed" or reloaded.get("error")
    ):
        raise SystemExit("Codex++ rejected the user-script reload")
    summary = session.evaluate("""(async () => {
      const policy = window.__codexPlusMaxTierPolicy;
      if (!policy) throw new Error("MAX policy was not loaded");
      await policy.ready;
      const state = await policy.sync();
      const settings = await window.__codexSessionDeleteBridge("/settings/get", {});
      const targets = policy.targetModels;
      const profiles = settings.relayProfiles || [];
      if (!profiles.length) throw new Error("No relay profiles available");
      let nativeMaxRules = 0;
      const invalidRules = [];
      for (const profile of profiles) {
        let metadata;
        try {
          metadata = JSON.parse(profile.modelMetadata || "{}");
          if (!metadata || typeof metadata !== "object" || Array.isArray(metadata))
            throw new Error();
        } catch {
          invalidRules.push({profile: profile.id, error: "Invalid metadata"});
          continue;
        }
        for (const slug of targets) {
          const entry = metadata[slug];
          const levels = entry?.supported_reasoning_levels;
          const valid = Array.isArray(levels)
            && levels.some(item => item?.effort === "max")
            && levels.some(item => item?.effort === entry.default_reasoning_level);
          if (valid) nativeMaxRules++;
          else invalidRules.push({profile: profile.id, model: slug});
        }
      }
      return {...state, version: policy.version, profiles: profiles.length,
        expectedRules: profiles.length * targets.length, nativeMaxRules,
        invalidRules};
    })()""")
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    if not isinstance(summary, dict) or summary.get("lastError"):
        raise SystemExit("MAX policy initialization failed")
    if summary["invalidRules"] or summary["nativeMaxRules"] != summary["expectedRules"]:
        raise SystemExit("Native MAX coverage is incomplete")
finally:
    session.close()
'@ | python -
```

Verify the saved settings file separately with a structured JSON parser,
emitting only profile counts, target-rule counts, and invalid profile IDs.
The expected rule count is dynamic. Check source/installed hashes and policy
version together. On a subsequent sync or hot reload, unchanged profiles should
not trigger another settings write; counters reset when the script is reloaded.

`tiers.py patch` is limited to the active profile and requires the model to
exist in its catalog. It preserves config newline format and avoids unchanged
config writes. Its offline fallback does not establish that the app is stopped:
check this before invoking a non-dry-run patch when the bridge is unavailable.

For inactive catalogs, enumerate each profile's referenced path and existing
canonical `<profile-id>.json` path, deduplicating resolved paths. Do not create
missing catalogs. Back up files before using `load_catalog`, `find_model`, and
`write_catalog` from `scripts/tiers.py`. Copy only persisted target reasoning
fields into an existing target entry, preserving other model fields. For an
ad hoc add-only update, `build_catalog(catalog, slug, ["max"], None)` preserves
the catalog's existing default. It mutates the supplied catalog object.

To validate an inactive catalog without touching the active config, pass a
per-process override to the discovered Codex executable:

```text
codex -c 'model_catalog_json="C:/absolute/path/to/relay-id.json"' debug models
```

Use `tiers.find_codex_cli()` to locate the binary if it is not on PATH. When
using Python `subprocess`, pass separate arguments and construct the TOML string
value with JSON quoting rather than building a shell command. Parse the returned
models and confirm the exact slug and `max`; an exit code alone is insufficient.

## Process relationship

```
codex-plus-plus-manager.exe
└── codex-plus-plus.exe --debug-port N --helper-port M
    └── ChatGPT.exe  (the Codex desktop app)
```

Terminating `codex-plus-plus.exe` therefore ends the user's session. Batch
restart work accordingly, and prefer asking the user to restart over killing the
tree.

## Upstream tier support

Local tier visibility does not establish relay API capability. Send a minimal
Responses request with the requested effort to check acceptance. Only the
explicit `usage.output_tokens_details.reasoning_tokens` field measures reported
reasoning tokens. Total output tokens cannot be used as a substitute, and one
HTTP success cannot prove that two efforts receive different reasoning budgets.

The active provider accepted `gpt-6.1-terra` with `reasoning.effort=max` during
the 2026-11-04 repair and reported 27 reasoning tokens. Other providers must
still support the exact requested model and effort.

## Observed Repair Evidence

This is historical evidence from 2026-11-04, not a substitute for fresh checks
or a fixed number of profiles for future runs.

| Check | Observed result |
| --- | --- |
| Installed application/policy | Codex++ 1.6.0 / policy 1.0.1 |
| Native settings coverage | 24 profiles, 48 target rules containing MAX |
| Regression tests | 13 JavaScript tests and 1 Python test passed |
| Fresh CLI catalog/model checks | 8 checks passed across existing target-bearing catalogs |
| Actual script hot reloads | 2 completed, retained all 48 rules without extra settings writes |
| Inactive catalogs synchronized | `relay-msh1tvzd`, `relay-mu40zaiy`, `relay-mu9ib5l0` |
| Config preservation | `config.toml` byte-identical to the pre-repair backup |
| Real provider switch/full restart | Not performed during the repair conversation |

API observations used the exact snapshots, without modifying credentials,
provider URLs, group choices, model lists, or context limits:

- `relay-mrwxcahx` accepted `gpt-6.1-terra` with MAX and reported 27 reasoning
  tokens.
- `relay-msh1tvzd` accepted `deepseek-v4.1-flash-1017` with MAX, without a
  separate reported reasoning-token count.
- `relay-mu40zaiy` initially returned HTTP 404 / `model_not_found` for both
  DeepSeek LOW and MAX. After the user changed its API group, the same exact
  slug completed with HTTP 200 for both efforts. LOW reported 22 reasoning
  tokens and 24 output tokens; MAX reported 12 reasoning tokens and 14 output
  tokens. These small requests demonstrate acceptance, not a larger MAX budget.

The original private repair report and backups are under
`~/.codex-session-delete/backups/reasoning-max-20261104-200611/`. The original
report's 404 predates the group change; retain it as historical evidence rather
than treating it as the relay's current status. Completion remains "persistent
repair deployed; real switch/full-restart acceptance pending" until actual
user-driven lifecycle checks are recorded.

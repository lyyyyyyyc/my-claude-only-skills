---
name: codex-plus-reasoning-tiers
description: |-
  Restore missing reasoning-effort tiers in Codex++ relay profiles, including MAX disappearing after provider switches or restarts. Use for Codex++ / 中转站 model-catalog and tier-persistence problems, not ordinary Codex model selection.
metadata:
  short-description: Fix Codex++ reasoning tier lists
---

# Codex++ Reasoning Tiers

Codex++ regenerates model catalogs when starting or switching providers.
The durable input is each profile's native `modelMetadata`, not a generated
catalog or a standalone `config.toml` edit. This workflow was checked against
Codex++ 1.6.0 on Windows. Recheck the generator and script lifecycle after upgrades.

Choose the scope:

- One model in the active profile: diagnose, back up, then use `tiers.py patch`.
- Persistence across providers and restarts: follow the whole workflow below.
  The bundled global policy targets exactly `deepseek-v4.1-flash-1017` and
  `gpt-6.1-terra`. It does not grant tiers to every model.
- Documentation-only requests: update the skill and validate it without
  reinstalling scripts, changing providers, making API calls, or restarting apps.

## 1. Diagnose The Effective State

Use PowerShell on Windows. Resolve commands from this skill's directory:

```powershell
$SkillRoot = Join-Path $env:USERPROFILE '.codex\skills\codex-plus-reasoning-tiers'
Set-Location -LiteralPath $SkillRoot
python scripts/tiers.py status --model deepseek-v4.1-flash-1017
python scripts/tiers.py status --model gpt-6.1-terra
python scripts/cdp.py
```

Record the installed version, `activeRelayId`, exact model slugs, profile model
lists, effective catalog path, native metadata, catalog efforts, and fresh CLI
efforts. Honor `CODEX_HOME` when resolving config and catalogs.

Interpret the layers separately:

- A model absent from the selected provider's list is not a missing-tier bug.
  Do not insert it or substitute a similarly named snapshot.
- Generic catalogs commonly contain only `low/medium/high/xhigh`.
- UI-only metadata does not override those native efforts.
- The CLI result shows what a fresh Codex process loads. It does not prove the
  already-running desktop process reloaded its catalog. A skipped CLI check is
  unverified, not a pass.
- `cdp.py` reports bridge availability in JSON. Inspect `available`; a zero exit
  code alone is not proof that the bridge is usable.

Read [references/mechanism.md](references/mechanism.md) for path resolution,
generator behavior, bridge recipes, and the observed repair evidence. Compare
manager switch/backfill logs when a catalog pointer changes.

## 2. Back Up Before Mutation

Create a timestamped private directory under
`~/.codex-session-delete/backups/`. Copy `settings.json`, effective `config.toml`,
the existing installed policy if present, and every catalog that will be changed.
Back up skill files or helpers too if modifying them. Record original paths and
hashes so unrelated changes can be distinguished later.

Settings and auth backups contain credentials. Never print their full contents,
include them in reports, or commit them.

While Codex++ runs, settings mutations must go through
`window.__codexSessionDeleteBridge("/settings/set", partialSettings)`.
Direct disk edits can be overwritten by the app's in-memory settings.

**If the bridge is unavailable while any relevant app/manager process is still
running, stop before patching.** `tiers.py patch` has a direct-file fallback;
bridge failure is not permission to use that fallback against live state.
Restore bridge access or arrange a user-driven shutdown first. Offline writes
are appropriate only after shutdown is confirmed, with a backup.

## 3. Use Native Metadata

The profile's `modelMetadata` is a JSON string containing this schema:

```json
{
  "exact-model-slug": {
    "default_reasoning_level": "max",
    "supported_reasoning_levels": [
      {"effort": "high", "description": "High"},
      {"effort": "max", "description": "Maximum reasoning"}
    ]
  }
}
```

Native fields are `supported_reasoning_levels`, `default_reasoning_level`, and
item `effort`. Renderer fields `supportedReasoningEfforts`,
`defaultReasoningEffort`, and item `reasoningEffort` are a different schema.
The generator may copy those unknown UI fields without replacing its native
four-tier list, making a broken patch look successful.

Preserve existing efforts, valid defaults, unrelated metadata, credentials,
URLs, context limits, and model lists. Do not replace malformed metadata with
an empty object. Diagnose the invalid entry without echoing its contents.
`apply_model_metadata_overrides` consumes native fields on catalog rebuilds.

## 4. Test And Deploy The Global Policy

Run the bundled regressions before installing a changed policy:

```powershell
node --test scripts/test_max_tier_policy.cjs
python -m unittest discover -s scripts -p test_tiers.py -v
```

Coverage includes native persistence, legacy migration, unrelated-field
preservation, defaults, exact slugs, case aliases, new profiles, idempotency,
bridge replacement, cleanup, and malformed metadata. Simulated document
lifecycles are regression tests, not actual application restarts.

After backup and successful tests, install the tested source:

```powershell
$ScriptDir = Join-Path $env:APPDATA 'Codex++\user_scripts'
New-Item -ItemType Directory -Path $ScriptDir -Force | Out-Null
$InstalledPolicy = Join-Path $ScriptDir '00-max-tier-policy.js'
Copy-Item -LiteralPath '.\scripts\max-tier-policy.js' -Destination $InstalledPolicy
Get-FileHash -LiteralPath '.\scripts\max-tier-policy.js', $InstalledPolicy
```

Check that source and installed hashes match. Through the live bridge, call
`/user-scripts/reload`, then await `window.__codexPlusMaxTierPolicy.ready`,
inspect `lastError`, and call `sync()`. Use the executable bridge recipe in
[references/mechanism.md](references/mechanism.md#deployment-bridge-recipe).
Reloading alone without checking policy state is not deployment verification.

The policy adds both native rules to every profile, even if its current model
list lacks a target, without adding that model to the list. It normalizes
settings writes and repairs newly added profiles on subsequent settings reads.
It preserves a valid existing default; otherwise its fallback is `max`.

Audit disk persistence as well as live state: for `N` profiles expect `2 * N`
native target rules containing `max`, with no invalid entries. Do not hardcode
the historical count of 24 profiles. Backend settings normalization may mirror
profiles into `tools.codex.relayProfiles`; do not overwrite unrelated `tools`
settings to maintain that mirror manually.

The UI overlay only supplies metadata for exact target models already listed
by the provider. It does not add models or reload a running Codex catalog.
The policy handles bridge reconnection and hot-reload cleanup and uses no
polling timer, scheduled task, or background service.

## 5. Synchronize And Verify Existing Catalogs

Global `sync()` persists settings; it does not rewrite every generated catalog.
For each requested model already in the active catalog, use the bundled patcher
after confirming bridge access:

```powershell
$Model = 'gpt-6.1-terra'
python scripts/tiers.py patch --model $Model --add max --default max --dry-run
python scripts/tiers.py patch --model $Model --add max --default max
python scripts/tiers.py status --model $Model
```

Repeat for DeepSeek only when that exact snapshot is listed. Omit `--default`
when only adding an effort and preserving the current default is intended.
This command patches one active profile, not all providers; the global policy
in step 4 supplies the cross-provider persistence.

Inspect both referenced catalogs and existing canonical
`model-catalogs/<profile-id>.json` files for inactive profiles. If immediate
consistency is needed, back them up and synchronize only existing target
entries' native reasoning fields from their profile rules. Use structured JSON
and the bundled catalog helpers, preserving every unrelated field. Skip absent
files and models; normal generation will apply native overrides later.

Verify a fresh CLI load for each inspected catalog using an explicit
`model_catalog_json` override, without switching the live provider just to test.
Require `max` in native metadata, catalog, and CLI output. Compare unrelated
fields against backups and check that config has no unintended changes.

Do not create `-tiers.json` sidecars or change paths to evade regeneration.
The entire `model-catalogs/` directory is managed, regardless of filename.
Provider switching restores the canonical pointer and manager backfill can
propagate it. Catalog-only and config-only patches are not durable fixes.

## 6. Test The Selected Upstream Separately

When API testing is within the user's request, reread the selected profile's
current endpoint and credentials privately. Send minimal Responses requests
for the exact slug with `reasoning.effort=low` and `reasoning.effort=max`,
changing only the effort. Do not test a cached group or substitute model.

Record provider/profile, date, exact slug, HTTP status, completion status,
sanitized error code, and reported `usage.output_tokens_details.reasoning_tokens`
when available. Do not infer reasoning tokens from total output tokens.

If both efforts return `model_not_found`, investigate group/model availability,
not local tier metadata. After the user changes a group, reread current settings
and repeat the same pair once. Preserve the earlier failure as historical
evidence and append the new result. Stop on a reproducible failure rather than
looping, changing accounts, or altering upstream groups without authorization.

HTTP success proves that the current upstream accepts the parameter. It does
not prove that MAX receives a larger budget or identical behavior on every
provider. A local tier list cannot supply an upstream's unavailable model.

## 7. Perform Real Switch And Restart Acceptance

Coordinate this with the user. Do not terminate `codex-plus-plus.exe`: it parents
the current desktop app and ends the conversation. A script hot reload is not a
full restart, and a newly launched CLI is not the running desktop process.

1. Have the user select a provider listing one target and use Codex++'s normal
   restart-Codex action. Reconnect to the new page rather than reusing an old CDP
   target.
2. Rerun `status` for both exact slugs. For each listed target, confirm native
   metadata, catalog, fresh CLI, actual picker MAX, and loaded policy/no error.
   An unlisted target is not applicable, not a successful model check.
3. Switch to a provider listing the other target, restart through Codex++,
   and repeat. Switch back and repeat at least once to test recurrence.
4. For a new profile, verify its native rules after the next settings read and
   repeat real startup acceptance. If generation preceded the first repair,
   regenerate/restart through the normal workflow before claiming native load
   success. A UI overlay alone does not establish this.

Report test count and actual lifecycle actions, never "unlimited restarts
verified." New app versions, disabled scripts, replaced settings, and upstream
changes require revalidation.

Use these completion labels explicitly:

| Label | Evidence required |
| --- | --- |
| Persisted/deployed | Native rules saved, installed hash matches, policy ready without error |
| Catalog/CLI verified | Matching native, on-disk, and fresh CLI efforts for the inspected models |
| API accepted | Current provider/group completes the exact slug and effort request |
| Switch/restart accepted | Actual user-driven switches/restarts and post-restart UI/native checks |

If the last row has not occurred, say "persistent repair deployed; real
switch/full-restart acceptance pending." Do not turn unit tests, hot reloads,
or API acceptance into a claim of complete lifecycle verification.

## 8. Recover Without Reverting User Changes

If the policy fails, preserve the sanitized error and stop further mutations.
Back up its current state. Move the installed policy outside `user_scripts`
or restore the previous script, then reload and confirm cleanup before restoring
metadata; otherwise it will immediately reapply its rules.

With the app running, fetch fresh settings and restore only this repair's
target metadata fields through `/settings/set`. Preserve newly changed groups,
credentials, profile additions, and unrelated edits. Restore only attributable
catalog/config fields from backups. Do not replace the whole settings file
with an old backup unless a coordinated full restore is explicitly intended.

Offline restoration requires confirmed shutdown. After recovery, rerun
diagnostics and state which checks remain pending. Keep backup locations private.

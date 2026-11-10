---
name: recover-plugings
description: |-
  Recover Codex plugins after switching between ChatGPT login and API-key/custom-provider auth. Use this when Codex plugins disappear from the @ menu, only bundled plugins like LaTeX appear, API-key login shows openai-api-curated instead of openai-curated, connector plugins such as GitHub/Google Drive do not show, or Codex fails with image_generation 403 after config changes. This skill emphasizes safe diagnosis, backups, minimal config edits, and read-only verification before changing auth or plugin settings.
metadata: {}
---

# Recover Plugings

## Purpose

Use this skill to recover Codex plugin availability without breaking normal chat. Treat plugin recovery as a multi-layer debugging problem: auth mode, model provider config, plugin marketplace, plugin install state, feature flags, running app-server processes, and tool-level verification can each disagree.

Keep the workflow conservative. First prove what layer is broken, then make the smallest reversible change.

## Safety Rules

- Do not print API keys, ChatGPT tokens, GitHub tokens, refresh tokens, or OAuth secrets.
- Back up `C:\Users\LX\.codex\config.toml` and `C:\Users\LX\.codex\auth.json` before any edit.
- Prefer `codex plugin add` and `codex features disable` over hand-writing large plugin blocks.
- Use the VS Code extension Codex binary when `codex` resolves to WindowsApps and fails with `Access is denied`.
- Do not pipe huge `codex debug prompt-input` or app-server output through `Select-String` unless output is redirected first; broken stdout pipes can cause noisy Rust panics.
- For tool tests, start with read-only checks: list plugins, list windows, search public GitHub issues, or return `OK`.

## Known Failure Patterns

### API key auth changes plugin catalogs

When Codex is logged in using only an API key, `codex plugin marketplace list` may show `openai-api-curated`. ChatGPT-scoped connector plugins such as `github@openai-curated` and `google-drive@openai-curated` may not appear in the UI even if their local plugin files exist.

Connector-style plugins often contain `apps = "./.app.json"` in `.codex-plugin/plugin.json`. These can require ChatGPT account or remote connector auth. Bundled local plugins such as `latex@openai-bundled`, `browser@openai-bundled`, `chrome@openai-bundled`, and `computer-use@openai-bundled` are more likely to work locally.

### Image generation 403 breaks chat

If the model provider is a custom API such as `https://ai-tokens.vip`, Codex may fail with:

```text
unexpected status 403 Forbidden: Image generation is not enabled for this group
```

The minimal safe fix is usually:

```toml
[features]
image_generation = false
```

Verify with a real model call after disabling it.

### PATH can point to the wrong codex.exe

On this machine, `Get-Command codex -All` may resolve first to:

```text
C:\Program Files\WindowsApps\OpenAI.Codex_...\app\resources\codex.exe
```

That binary can return `Access is denied` from PowerShell. Use the VS Code extension binary instead:

```powershell
& 'c:\Users\LX\.vscode\extensions\openai.chatgpt-26.5616.51431-win32-x64\bin\windows-x86_64\codex.exe' --version
```

If the extension version changes, discover the current path with:

```powershell
Get-ChildItem -LiteralPath 'C:\Users\LX\.vscode\extensions' -Directory |
  Where-Object { $_.Name -like 'openai.chatgpt-*' } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1
```

## Recovery Workflow

### 1. Snapshot current state

Run read-only checks first:

```powershell
$Codex = 'c:\Users\LX\.vscode\extensions\openai.chatgpt-26.5616.51431-win32-x64\bin\windows-x86_64\codex.exe'
& $Codex --version
& $Codex login status
& $Codex features list
& $Codex plugin marketplace list
& $Codex plugin list
```

Check auth shape without printing secrets:

```powershell
$auth = 'C:\Users\LX\.codex\auth.json'
$j = Get-Content -Raw -LiteralPath $auth | ConvertFrom-Json
[pscustomobject]@{
  auth_mode = $j.auth_mode
  has_openai_api_key = [bool]$j.OPENAI_API_KEY
  has_tokens = [bool]$j.tokens
  last_refresh = $j.last_refresh
} | Format-List
```

Check whether connector plugins have app metadata:

```powershell
$p = 'C:\Users\LX\.codex\.tmp\plugins\plugins\github\.codex-plugin\plugin.json'
$j = Get-Content -Raw -LiteralPath $p | ConvertFrom-Json
[pscustomobject]@{
  name = $j.name
  displayName = $j.interface.displayName
  hasApps = [bool]$j.apps
  defaultPromptCount = @($j.interface.defaultPrompt).Count
}
```

### 2. Back up before editing

```powershell
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
Copy-Item -LiteralPath 'C:\Users\LX\.codex\config.toml' -Destination "C:\Users\LX\.codex\config.toml.backup_before_plugin_recovery_$ts"
Copy-Item -LiteralPath 'C:\Users\LX\.codex\auth.json' -Destination "C:\Users\LX\.codex\auth.json.backup_before_plugin_recovery_$ts"
```

If the user has a known-good ChatGPT auth backup such as `auth-chatgpt-backup.json` or a localized copy name, inspect it without printing tokens:

```powershell
$p = 'C:\Users\LX\.codex\auth-chatgpt-backup.json'
$j = Get-Content -Raw -LiteralPath $p | ConvertFrom-Json
[pscustomobject]@{
  auth_mode = $j.auth_mode
  has_tokens = [bool]$j.tokens
  has_refresh_token = [bool]$j.tokens.refresh_token
  last_refresh = $j.last_refresh
}
```

### 3. Fix the image-generation crash first

If chat fails with image generation 403, disable the feature before doing plugin experiments:

```powershell
& $Codex features disable image_generation
```

If the command is unavailable, add or update this in `config.toml`:

```toml
[features]
image_generation = false
```

Verify:

```powershell
& $Codex features list | Select-String -Pattern '^image_generation\s'
& $Codex exec --skip-git-repo-check --ephemeral 'Reply with exactly OK and no explanation.'
```

### 4. Reinstall missing local plugin records

Use the plugin manager rather than manually composing sections:

```powershell
& $Codex plugin add browser@openai-bundled
& $Codex plugin add chrome@openai-bundled
& $Codex plugin add computer-use@openai-bundled
& $Codex plugin add latex@openai-bundled
```

For ChatGPT-scoped curated plugins:

```powershell
& $Codex plugin add github@openai-curated
& $Codex plugin add google-drive@openai-curated
& $Codex plugin add superpowers@openai-curated
& $Codex plugin add hugging-face@openai-curated
```

Confirm install state:

```powershell
& $Codex plugin list | Select-String -Pattern 'installed, enabled|Marketplace `'
```

Expected config sections look like:

```toml
[plugins."github@openai-curated"]
enabled = true

[plugins."computer-use@openai-bundled"]
enabled = true
```

### 5. Understand API-key vs ChatGPT tradeoff

If the user needs ChatGPT connector plugins in the UI, pure API-key auth may not be enough. The practical split is:

- ChatGPT auth in `auth.json` controls ChatGPT-scoped plugin catalog and connector identity.
- `model_providers.OpenAI.env_key = "OPENAI_API_KEY"` can direct model calls to an API key.
- Do not combine `requires_openai_auth = true` and `env_key` for the same custom provider. `requires_openai_auth = true` means the provider expects OpenAI/Codex account auth.

A custom provider block usually looks like:

```toml
[model_providers.OpenAI]
name = "OpenAI"
base_url = "https://ai-tokens.vip"
wire_api = "responses"
env_key = "OPENAI_API_KEY"
```

Only restore ChatGPT auth from a backup after explaining the tradeoff to the user and confirming that the backup token is still valid. After changing auth or provider config, restart the Codex UI/app-server.

## Verification Recipes

### Verify chat still works

```powershell
& $Codex exec --skip-git-repo-check --ephemeral 'Reply with exactly OK and no explanation.'
```

Success means the model request path works. Warnings about MCP timeouts or remote plugin catalog can still appear; distinguish warnings from fatal errors.

### Verify Computer Use

First check plugin state:

```powershell
& $Codex plugin list | Select-String -Pattern 'computer-use@openai-bundled'
& $Codex features list | Select-String -Pattern '^computer_use\s'
```

In a live Codex session, use the `node_repl` tool if available:

1. Add the real runtime module directory:

```text
C:\Users\LX\AppData\Local\OpenAI\Codex\runtimes\cua_node\<hash>\bin\node_modules
```

2. Import `@oai/sky`.
3. Inspect exported methods.
4. Run only read-only `sky.list_windows()` first.

Working output should include desktop windows and methods like `list_windows`, `launch_app`, `click`, `type_text`, and `press_key`.

### Verify GitHub

The GitHub plugin can be useful through MCP even if the ChatGPT connector chip does not show in the UI.

Read-only checks:

```powershell
gh auth status
& $Codex mcp list | Select-String -Pattern 'github'
```

In a live Codex session, use the GitHub MCP tool for a public read-only query, for example searching issues in `openai/codex`. Do not create issues, PRs, or comments for a capability test.

### Verify UI refresh

If CLI state is correct but `@` does not show plugins:

- Restart the Codex desktop app or reload the VS Code window.
- Kill stale `codex.exe app-server` processes only if the user agrees or the UI is already closed.
- Try typing a specific mention, such as `@github`, `@computer`, `@chrome`, or `@latex`, instead of only pressing a blank `@`.
- Remember that connector plugins may be hidden under API-key auth even when local plugin files are installed.

## Interpreting Results

- `installed, enabled` in `codex plugin list` proves local install state, not cloud connector authorization.
- A successful MCP read query proves tool usability even if the UI chip is absent.
- `api key auth is not supported` for remote plugin catalog explains why ChatGPT connector discovery can fail under API-key auth.
- `Unsupported` in `codex mcp list` auth column is normal for many stdio MCP servers; it does not by itself mean the MCP is broken.
- `Access is denied` when running `codex` often indicates the PATH points to WindowsApps; call the VS Code extension binary directly.

## Final Report Template

When done, summarize:

```text
Plugin recovery result:
- Model requests: working / not working
- image_generation: disabled / unchanged
- Plugin marketplaces: openai-bundled / openai-curated / openai-api-curated
- Local plugins: list key plugins that are installed, enabled
- @ menu: list visible plugins and plugins hidden by API-key or connector limits
- Computer Use verification: whether list_windows succeeded
- GitHub verification: whether MCP search or gh auth succeeded
- Backup files: list config/auth backup paths
- User action still needed: restart Codex, log in with ChatGPT, or reauthorize GitHub/Google Drive
```

---
name: add-mcp
description: |-
  Add MCP servers to the VS Code Codex extension by writing `mcp_servers` entries into `C:\Users\LX\.codex\config.toml` and verifying in the MCP panel. Use when the user says "给我添加这个mcp到你的codex里面去", "给我添加这个mcp", or asks to add/enable/migrate MCP servers for Codex, including installing an MCP from GitHub.
metadata: {}
---

# Add MCP to Codex (VS Code)

## Goal
Add one or more MCP servers so they show in the Codex MCP panel and can be used in new chats.

## Inputs needed
- Server name (short id)
- Command + args to start the server (from existing config or repo README)
- Any required env vars (tokens)
- Whether the server needs a stdio proxy (framed protocol)

## Workflow
1. Open `C:\Users\LX\.codex\config.toml`.
2. Add an entry under `mcp_servers` (NOT `mcp.servers`). Example:

```toml
[mcp_servers.github]
command = "npx"
args = ["-y", "<package-or-exe>", "..."]
```

3. If the server speaks framed JSON-RPC (not plain stdio), wrap it with the proxy (only if you have it):

```toml
[mcp_servers.some_server]
command = "python"
args = ["C:/Users/LX/.codex/bin/mcp-stdio-proxy.py", "--", "<original-cmd>", "<arg1>"]
```

4. Reload VS Code window: `Developer: Reload Window`.
5. Open the MCP panel and verify the server shows as Enabled.
6. Run a quick tool call to validate (e.g., GitHub search repo).

## Common sources
### A) Migrate from Claude `.mcp.json`
- Copy the server name, command, and args.
- Convert to `[mcp_servers.<name>]` in `config.toml`.
- If a name conflicts with an existing Codex server, keep the Codex one and rename the new entry.

### B) Install from GitHub
- Read the repo README and follow its install/run steps.
- Typical patterns:
  - Node: `npx -y <package>`
  - Python: `pipx`/`uvx` or `python -m <module>`
- Add the resulting command/args into `mcp_servers`.
- Add env vars if required (tokens).

## Troubleshooting
- MCP panel empty: ensure you used `mcp_servers` and reloaded VS Code.
- Server shows but tools fail: run the command in a terminal to see stderr; fix missing runtimes or bad args.
- Windows paths: use full paths for executables if they are not on PATH.

## Notes
- Codex VS Code extension reads `C:\Users\LX\.codex\config.toml`.
- `.mcp.json` is not used by Codex and will not show in the MCP UI.

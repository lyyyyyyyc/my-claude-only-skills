---
name: recovery-codex-history
description: |-
  Recover missing Codex Desktop local chat history after the user switches API relay, provider, model, API key, auth mode, or account and says phrases like "缁欐垜鎭㈠鎴戠殑CODEX鑱婂ぉ璁板綍", "Codex鑱婂ぉ璁板綍娌′簡", "鎹腑杞悗鍘嗗彶娑堝け", "鎭㈠Codex鍘嗗彶璁板綍", or "渚ц竟鏍忕湅涓嶅埌浠ュ墠鐨勫璇?. Use this skill whenever Codex history disappeared after config/login/provider changes. It wraps GODGOD126/codex-history-sync-tool with status, backup, and sync safeguards.
metadata: {}
---

# Codex History Recovery

Use this skill when the user wants to recover Codex Desktop conversations that disappeared from the sidebar after switching relay/API/provider/model/auth/account settings.

This skill is for **local history visibility recovery**. It can only help when the conversation files still exist under the user's local Codex data directory, usually `%USERPROFILE%\.codex`. Do not promise cloud-account recovery or recovery of deleted files.

## What The Skill Should Do

When the user says something like `缁欐垜鎭㈠鎴戠殑CODEX鑱婂ぉ璁板綍`, treat it as a request to:

1. Check the local Codex data directory.
2. Ensure the upstream helper repo exists locally.
3. Run `status` to inspect current history/provider/model state.
4. Run `backup` before changing anything, storing backups in `D:\CodexHistoryBackups`.
5. Run `sync` to attach old local conversations to the current provider/model metadata.
6. Tell the user to restart Codex Desktop and re-open the original project folder if needed.

## Upstream Tool

Use this GitHub project:

- Repository: `GODGOD126/codex-history-sync-tool`
- URL: `https://github.com/GODGOD126/codex-history-sync-tool`
- Purpose: sync local Codex Desktop conversation history back to the current provider/model.

Do not reimplement the database-editing logic. Use the upstream tool's `sync_backend.py` through the bundled wrapper script. The wrapper patches only the upstream backup directory assignment at runtime so backups go to `D:\CodexHistoryBackups`; it does not edit the user's Codex config or delete history.

## Safety Rules

- Never print API keys, tokens, refresh tokens, client secrets, provider headers, or the full contents of `config.toml`.
- Do not edit `C:\Users\LX\.codex\config.toml` unless the user explicitly asks.
- Do not delete any Codex history files.
- Always run `status` before `sync`.
- Always run `backup` before `sync`.
- If `.codex` is missing, stop and report that local Codex data was not found.
- If the local history files are already deleted, explain that this tool cannot reconstruct deleted conversations.
- If the user asks for `restore`, first create/confirm a backup, then run the upstream `restore` command.
- If commands fail, report the failing step and the exact non-secret error summary.

## Preferred Execution

Run the bundled wrapper from this skill directory:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\LX\.codex\skills\recovery-codex-history\scripts\run_codex_history_recovery.ps1" -Action Full
```

`-Action Full` performs:

1. Clone/update `https://github.com/GODGOD126/codex-history-sync-tool`.
2. Run `status`.
3. Run `backup`.
4. Run `sync`.

The wrapper defaults to storing the helper repository at:

```text
%USERPROFILE%\.codex-history-sync-tool
```

The wrapper stores backups at:

```text
D:\CodexHistoryBackups
```

The wrapper creates this folder automatically if it does not exist. Do not move new backups back into `%USERPROFILE%\.codex\history_sync_backups` unless the user explicitly asks.

## Useful Commands

Status only:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\LX\.codex\skills\recovery-codex-history\scripts\run_codex_history_recovery.ps1" -Action Status
```

Backup only:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\LX\.codex\skills\recovery-codex-history\scripts\run_codex_history_recovery.ps1" -Action Backup
```

Custom backup folder, only if the user explicitly asks:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\LX\.codex\skills\recovery-codex-history\scripts\run_codex_history_recovery.ps1" -Action Backup -BackupDir "D:\CodexHistoryBackups"
```

Sync after a backup:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\LX\.codex\skills\recovery-codex-history\scripts\run_codex_history_recovery.ps1" -Action Sync
```

Open the upstream GUI:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\LX\.codex\skills\recovery-codex-history\scripts\run_codex_history_recovery.ps1" -Action Gui
```

Restore latest backup:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\LX\.codex\skills\recovery-codex-history\scripts\run_codex_history_recovery.ps1" -Action Restore
```

## How To Report Back

After running the workflow, answer in Chinese and include:

- Which action ran: `Status`, `Backup`, `Sync`, `Full`, `Gui`, or `Restore`.
- Where the upstream helper repo is located.
- Where backups are stored.
- Whether the command completed successfully.
- Next step: restart Codex Desktop; if history still does not show, open the original project folder where that conversation happened.

Example final response:

```text
宸茬粡鎸夋仮澶嶆祦绋嬭窇瀹岋細status -> backup -> sync銆?宸ュ叿鐩綍锛欳:\Users\LX\.codex-history-sync-tool
澶囦唤鐩綍锛欴:\CodexHistoryBackups

鐜板湪閲嶅惎 Codex Desktop銆傚鏋滃乏渚т粛鐒剁湅涓嶅埌鏃у璇濓紝鍏堝垏鍥炴棫瀵硅瘽鍘熸潵鐨勯」鐩洰褰曞啀鐪嬶紝鍥犱负鏂扮増 Codex 鍙兘鎸?cwd/project 杩囨护鍘嗗彶銆?```

## Failure Handling

If `git` is missing:

- Tell the user to install Git or manually download the repo ZIP.
- Do not continue with partial commands.

If Python is missing:

- Tell the user Python 3.10+ is required.
- Mention that the upstream README expects `py -3`.

If `sync` succeeds but the sidebar is still empty:

1. Tell the user to restart Codex Desktop.
2. Tell the user to open the old conversation's original workspace folder.
3. Run `Status` again if the user asks for further diagnosis.

## Test Prompts

Use these prompts to verify triggering and behavior:

- `[$recovery-codex-history] 缁欐垜鎭㈠鎴戠殑CODEX鑱婂ぉ璁板綍`
- `鎴戝垰鎹簡涓浆锛孋odex 宸﹁竟鍘嗗彶璁板綍绌轰簡锛屽府鎴戞仮澶峘
- `鍒囨崲 provider 鍚庝互鍓嶇殑 Codex 瀵硅瘽鐪嬩笉鍒颁簡锛屽厛澶囦唤鍐嶅悓姝

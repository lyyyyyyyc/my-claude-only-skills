---
name: add-skill
description: |-
  Add a Codex skill into C:\Users\LX\.codex\skills\local from GitHub, a local folder, or a .skill package. Use when the user says "给我添加这个skill", "给我安装这个skill", "把这个skill加到codex", or asks to add/enable/migrate skills. Always install into the Codex skills folder, not the current project.
metadata: {}
---

# Add Skill

## Goal

Install a skill so Codex can load it. Never place skills in the current workspace; always use `C:\Users\LX\.codex\skills\local`.

## Inputs to Collect

- Source type: GitHub URL, local folder path, or `.skill` file.
- Target skill name: prefer the `name` in `SKILL.md` frontmatter.

## Workflow

### 1) GitHub Repo

- Clone to a temp location under `C:\Users\LX\.codex\skills\_incoming`.
- Find the folder that contains `SKILL.md`.
- If multiple candidates exist, ask the user which one to install.
- Copy only the skill folder (with `SKILL.md` and any `scripts/`, `references/`, `assets/`) to `C:\Users\LX\.codex\skills\local\<skill-name>`.
- Preferred path: copy the original files directly. Do not retype files by hand unless direct copy is blocked.
- If any file from a GitHub skill is hand-written locally instead of directly copied, you MUST do a strict comparison against the original repository after installation.
- Strict comparison means comparing the full text of each hand-written file against the upstream original file, not just checking that the file exists or that the size looks similar.
- At minimum, compare `SKILL.md` and every hand-written file under `scripts/`, `references/`, `assets/`, or other copied subfolders.
- If strict comparison cannot be completed, do not claim the installed skill is identical to upstream. State clearly that installation succeeded but exact-content verification is incomplete.
- If strict comparison finds any difference, either fix the file until it matches or explicitly report which files differ and why.
- Remove the temp clone.

### 2) Local Folder

- Verify `SKILL.md` exists in the folder.
- Copy the folder to `C:\Users\LX\.codex\skills\local\<skill-name>`.

### 3) .skill Package

- Extract the `.skill` (zip) into `C:\Users\LX\.codex\skills\local`.
- Ensure the top-level folder name matches the skill name; rename if needed.

## Verification

- Confirm `C:\Users\LX\.codex\skills\local\<skill-name>\SKILL.md` exists.
- For GitHub installs that involved any hand-written reconstruction, record the strict comparison result before declaring success.
- If the skill does not appear, reload the Codex window and try again.

## 调用失败排障（新增）

当用户反馈“技能已安装但调用不了”时，按以下顺序排查，不要直接重装。

1. 先确认目标技能元数据
- 检查 `SKILL.md` frontmatter 至少包含 `name` 与 `description`。
- 检查 `agents/openai.yaml` 是否为合法 YAML（尤其是引号是否闭合）。
- 若发现乱码或非法字符，按 UTF-8 重新写入并复核。

2. 再确认 Codex 扫描路径是否可达
- 重点检查 `C:\Users\LX\.codex\skills\...` 与 `C:\Users\LX\.skillshub\...` 的联接是否断链。
- 若日志出现 `failed to stat skills entry ... (symlink)`，说明路径存在但目标丢失。

3. 无删除修复原则
- 不删除用户原有技能目录。
- 优先补“兼容联接”：把缺失的 `C:\Users\LX\.skillshub\<skill>` 指向 `C:\Users\LX\.skillshub\local\...` 下真实目录。
- 对用户自定义技能，再额外补一层 `C:\Users\LX\.codex\skills\<skill>` 入口，提升命中稳定性。

4. 最后做可执行验证
- 用 `codex exec` 做最小触发测试，例如：
  - ``$systematic-debugging 仅输出两个字：测试``
  - ``$math-modeling-data-preprocessing 仅输出两个字：可用``
- 若都能返回预期短文本，视为调用链已打通。

## 本次实际修复记录（2026-02-21）

1. 现象
- 用户反馈 `[$systematic-debugging](...)` 与自建数模预处理技能在 Codex 插件内无法调用。

2. 根因
- `Codex.log` 存在大量 `failed to stat skills entry ... (symlink)`。
- 旧联接指向 `C:\Users\LX\.skillshub\<skill>`，而实际技能主要位于 `C:\Users\LX\.skillshub\local\...`，导致断链。
- 个别技能文件元数据不规范（如 YAML 引号/字段问题）会进一步增加加载噪音。

3. 实施动作（未删除用户内容）
- 补齐 `C:\Users\LX\.skillshub\...` 到 `...\local\...` 的兼容联接（仅新增）。
- 补齐 `C:\Users\LX\.skillshub\systematic-debugging` 联接。
- 为用户自定义技能补齐：
  - `C:\Users\LX\.skillshub\math-modeling-data-preprocessing`
  - `C:\Users\LX\.codex\skills\math-modeling-data-preprocessing`
- 统一确认技能名为 `math-modeling-data-preprocessing`，并修复其 `agents/openai.yaml` 为合法 UTF-8 YAML。

4. 验证结果
- `codex exec` 成功触发 `$systematic-debugging`，返回“测试”。
- `codex exec` 成功触发 `$math-modeling-data-preprocessing`，返回“可用”。

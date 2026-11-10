
# Claude Code 技能库

本仓库提供 **669 个默认技能**和 **128 个可选版本**，共 **797 个不同的技能包**。
保留论文检索、文献数据库、引用管理和写作相关技能。私人账号和身份配置已排除。
仓库公开期间可匿名下载，不需要 GitHub CLI、GitHub 登录或 token。

## Windows 云服务器安装

在使用 Claude Code 的 **Administrator PowerShell** 中执行：

```powershell
git clone https://github.com/lyyyyyyyc/my-claude-only-skills.git C:\CloudCode\SkillsRepo
Set-Location C:\CloudCode\SkillsRepo
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1 -Destination 'C:\Users\Administrator\.claude\skills'
```

已有克隆时先核对 origin 和本地修改，再运行 `git pull --ff-only`，随后重新执行安装器。
如果已有目录包含旧的私有仓库历史，请在新的独立目录下载公开版本，不强制重置或覆盖。

没有 Git 时，可从 GitHub 的 Code → Download ZIP 下载并解压，在解压后的仓库目录执行同一安装脚本。
使用官方 ZIP 地址：`https://github.com/lyyyyyyyc/my-claude-only-skills/archive/refs/heads/main.zip`。
ZIP 应解压到独立目录，避免与已有版本混合。

若云端 `CLAUDE_CONFIG_DIR` 与上面的默认目录不同，请把 Destination 改为其 `skills` 子目录。
不应安装到 SSM SYSTEM 用户的 profile。安装后重新开启 Claude Code 会话。

## 按需安装与更新

```powershell
.\scripts\install.ps1 -Destination 'C:\Users\Administrator\.claude\skills' -Name academic-paper,paper-lookup,anti-defensive-writing-en
.\scripts\install.ps1 -IncludeVariants -Name '目录中列出的完整版本名称'
```

默认只安装 669 个主版本，variants 不自动安装。安装器核对完整文件哈希，相同内容跳过。
已管理且未被修改的版本可以更新，旧内容保留在 `.cloud-skills-backups`。
其他来源或本地修改的同名技能将跳过，不覆盖。状态保存在 `.cloud-skills-state.json`。
安装器不执行技能内部脚本、不安装全部依赖、不修改 Claude 登录或全局权限。

## 目录与验证

- [CATALOG.md](CATALOG.md)：完整技能目录。
- [COMPATIBILITY.md](COMPATIBILITY.md)：云端依赖及路径差异。
- [DEDUPLICATION.md](DEDUPLICATION.md)：去重与公开范围。
- `_meta/codex-export.json`：格式元数据、导出清单和文件哈希。
- [scripts/install.ps1](scripts/install.ps1)：Windows 安装器。
- [scripts/validate.py](scripts/validate.py)：格式与文件完整性验证。
- [scripts/security_check.py](scripts/security_check.py)：扫描与精确示例误报复核。

```powershell
uv run --with PyYAML python .\scripts\validate.py
python .\scripts\security_check.py --gitleaks 'gitleaks.exe'
```

各技能保留各自许可证，套件级许可证位于对应 `_upstream_licenses/`。
本集合不为第三方技能重新指定许可证。
检索服务的真实 API Key 和登录配置需在云服务器本地单独配置。

## Nature 系列

2026-11-10 核对 Yuan1z0825/nature-skills，固定提交 `a1a8220366e82ecd8584ea3d7f46cb3969f4b018`。新增导出 18 个已安装的 Nature 技能，其中 10 项有上游更新、8 项无内容更新。保留上游 Apache-2.0 及各包自带许可证。
Nature Downloader 未更新、未改动，也不加入本次公开导出。上游新增但本机未安装的其他 Nature 技能不自动安装。
详情见 [_meta/nature-upstream.json](_meta/nature-upstream.json)。

# 兼容性说明

技能正文、脚本和参考资料保持原样。安装器只复制技能文件，不安装 Python、Node、MCP、桌面软件或账户凭据。
涉及 Codex 工具、本机路径或其他软件的技能，需要按云端实际环境配置。安装成功不代表所有外部依赖均已可用。

| 静态依赖标签 | 包数 |
| --- | --- |
| `bash` | 38 |
| `codex-environment` | 17 |
| `desktop-or-specialist-software` | 11 |
| `local-paths` | 29 |
| `mcp-tools` | 42 |
| `node` | 8 |
| `powershell` | 6 |
| `python` | 202 |

默认安装 651 个主版本，128 个 variants 仅按需安装。
同一技能可能有多个标签。大量技能的描述会占用上下文，可用 -Name 按需安装。
云端请将目标设为实际 CLAUDE_CONFIG_DIR 下的 skills 目录，避免装入 SSM SYSTEM 用户目录。
API Key、账号登录和 MCP 授权需要在云服务器单独配置，不从本仓库提供。

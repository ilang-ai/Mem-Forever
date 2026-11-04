# env/ — machine environment, no secrets

What lives here and what `brain.py install` does with it:

| File | Content | Secrets |
|---|---|---|
| `settings.json` | Your agent CLI settings (Claude Code reads `~/.claude/settings.json`) | none; check before adding |
| `mcp.json` | MCP servers; every key field is written `${VAULT:name}` and filled from the unlocked vault at install time | placeholders only |
| `scheduled-tasks/` | Scheduled task definitions, one folder per task | placeholders only |
| `ssh_config.template` | Host aliases and jump hosts; private keys live in `vault/` | no keys |
| `install.ps1`, `install.sh` | New-machine checklist as a script: git, python, age, your agent CLI, then `brain.py vault unpack` and `brain.py install` | none |

Rule: anything that would let someone act as you goes into `vault/` (see `docs/VAULT.md`), never here. `python -X utf8 tools/brain.py check` scans this directory too.

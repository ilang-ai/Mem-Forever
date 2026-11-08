# env/ — the ledger and the machine environment

This directory is where the derivation starts. It lives in a **private** repository; `brain.py check` does not scan it for secret-like text, and `tools/hooks/pre-push` refuses to push it to a public remote.

| File | Content |
|---|---|
| `ledger.env` | the authorization ledger: one `::STATE{@name, door, kind, ref or value, verify, last_verified, recover, scope, top, why}` row per door; see [docs/LEDGER.md](../docs/LEDGER.md) |
| `pepper` | 32 random bytes (hex), written by `brain.py init`, committed; the encoded rows of `keys.env` are reversible with it and this tool, and with nothing else. Not encryption: a holder of the repository reads everything; it keeps keys out of grep, screenshots, model context and pastes |
| `keys.env` | `KEY=enc1:...` rows the ledger points at with `ref:KEY`, encoded at rest; written by `brain.py ledger add --value`, `ledger harvest`, `ledger encode`; `ledger decode` prints them plain for the owner |
| `otp.json` | hashes of one-time codes the owner issued for top doors; expires; ignored by git |
| `ssh/` | SSH private keys `migrate-2to3` brought over from a 2.1 vault, one ledger row each |
| `settings.json` | your agent CLI settings (Claude Code reads `~/.claude/settings.json`) |
| `mcp.json` | MCP servers; a key field may say `${VAULT:name}` and is filled from the ledger at install time |
| `scheduled-tasks/` | scheduled task definitions, one folder per task |
| `ssh_config.template` | host aliases and jump hosts |
| `install.ps1`, `install.sh` | new-machine checklist as a script: git, python, your agent CLI, then `brain.py install` and `brain.py ledger verify all` |

Rule: a key reaches a model's context only when a `next` item names its door (`brain.py unlock`) and this machine holds the owner's grant (`brain.py grant <DOOR>` or `--all`, git config, never in the repository; top doors keep the one-time code), never by reading this directory into the conversation. The pasted brain (`brain.py paste`) carries the ledger without values unless the owner says `--with-values`.

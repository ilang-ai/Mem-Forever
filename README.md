# mem-forever

**Every AI tool forgets you. Fork this repo and they never will again.**

[中文](docs/README.zh.md) | [日本語](docs/README.ja.md) | [한국어](docs/README.ko.md) | [Español](docs/README.es.md) | [Français](docs/README.fr.md) | [Deutsch](docs/README.de.md) | [Português](docs/README.pt.md) | [Русский](docs/README.ru.md)

---

You close a conversation. Everything you discussed is gone. Next session, you start from zero. Explain yourself again. Re-establish preferences. Watch the AI make the same mistakes you already corrected.

This repo is the fix. Your AI remembers who you are, what you decided, what you learned, and what you hate. Across every tool. Across every session. Forever.

## How it works

```
.ilang/
  soul.md      ← who you are (auto-generated, not by you)
  memory.md    ← what you decided, learned, built (auto-appended)
```

Your AI reads these files at the start of every session. Updates them at the end. Commits and pushes. Next session, next tool, next month, next year: full context, zero repetition.

## Setup (10 seconds)

**Step 1**: Click **"Use this template"** → **Create a new repository** → Set to **Private**.

**Step 2**: There is no step 2.

Open the repo with any AI tool. It reads the instructions, asks you a few questions, and starts building your profile. From that point on, it remembers.

## Use with any AI tool

### Claude Code / Codex / Cursor / Copilot / Gemini CLI

Open this repo in your tool. The instruction files are already in place:

| Tool | Auto-reads |
|---|---|
| Claude Code | `CLAUDE.md` |
| Codex | `AGENTS.md` |
| Cursor | `.cursorrules` |
| Copilot | `.github/copilot-instructions.md` |
| Gemini CLI | `GEMINI.md` |

### Working on a different project?

Tell your AI tool:

> My memory repo is at `https://github.com/YOUR_USERNAME/mem-forever`. PAT: `ghp_xxx`. Clone it, read `.ilang/soul.md` and `.ilang/memory.md`, then come back to this project.

That's it. One sentence. Full context restored.

### ChatGPT / Claude.ai / Gemini web

Upload `.ilang/soul.md` to:

| Platform | Where |
|---|---|
| ChatGPT | Project knowledge files |
| Claude.ai | Project knowledge |
| Gemini | Google Drive → Gemini reads it |

When memory updates, re-upload. Or just paste the content at the start of a conversation.

## What gets remembered

Your AI auto-generates and maintains two files:

**soul.md** is your profile. Built from conversation, not from a form. Contains your role, work style, preferences, anti-patterns, and lessons. Gets sharper every session through mutation and decay rules. Think of it as behavioral DNA that travels with you.

**memory.md** is your logbook. Decisions made, lessons learned, facts discovered, progress tracked. Append-only. Git history preserves everything.

You never write these files manually. Your AI does it. You can read and edit them anytime. They are plain text in your private repo. You own them.

## Multiple projects?

Use this template again. Create `mem-forever-work`, `mem-forever-side-project`, `mem-forever-research`. Each repo is an independent memory. Same engine, different context.

## Upstream updates

New features and improvements sync automatically every Monday via GitHub Action. Only engine files update. Your `.ilang/` data is never touched.

## Privacy

Your memory lives in a private GitHub repo that you own. No server. No account. No data leaves your repo. Delete the repo and it's gone.

## Comparison

| | mem-forever | Nowledge Mem | Mem0 |
|---|---|---|---|
| Install | Use template | Download app + configure | pip install + API key |
| Config | None | MCP + plugins + LLM setup | SDK integration |
| Storage | Your GitHub repo | Local SQLite | Cloud vectors |
| Cross-tool | Any tool that reads files | Plugin per tool | API per tool |
| Price | Free | Free / Pro | Free / Pro |
| Data ownership | You | You | Theirs |
| Migration | `git clone` | Export | API call |

## How it actually works

The instruction files (`CLAUDE.md`, `.cursorrules`, `AGENTS.md`, `GEMINI.md`) contain behavioral rules written in [I-Lang v3.0](https://ilang.ai), a structured protocol that AI models parse natively. These rules tell the AI how to extract preferences, format memories, handle conflicts, and evolve your profile over time.

You don't need to know I-Lang. You don't need to read the instruction files. You just talk to your AI and it gets better at working with you.

## License

MIT

---

Built by [I-Lang Protocol](https://ilang.ai). The native language of artificial intelligence.

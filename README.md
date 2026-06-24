---
license: mit
language:
  - en
  - zh
  - ja
  - ko
  - es
  - fr
  - de
  - pt
  - ru
tags:
  - i-lang
  - ai-memory
  - agent
  - cross-tool
  - persistent-memory
pretty_name: Mem-Forever
---

# Mem-Forever

> **永久记忆 · 跨会话 · 跨模型**
> A persistent memory layer for AI agents, built on the I-Lang protocol.
>
> I-Lang is the first protocol to formally map Greek mathematical symbols (Σ, Δ, φ, λ, Ω, ∇, μ, Π, ψ, ξ, ζ, θ, ∂) as primitive verbs for AI-to-AI communication, and the first to define a computable vector space for AI judgment (11 dimensions, 4 axioms).

[![License](https://img.shields.io/badge/license-MIT-d4a858?style=flat-square)](LICENSE)
[![Protocol](https://img.shields.io/badge/protocol-I--Lang_v4.0-d4a858?style=flat-square)](https://ilang.ai)
[![I-Lang L2](https://img.shields.io/badge/I--Lang-L2_Compatible-d4a858?style=flat-square)](https://github.com/ilang-ai/ilang-spec)
[![Tools](https://img.shields.io/badge/works_with-Claude_·_Cursor_·_Codex_·_Copilot_·_Gemini-d4a858?style=flat-square)]()

[中文](docs/README.zh.md) | [日本語](docs/README.ja.md) | [한국어](docs/README.ko.md) | [Español](docs/README.es.md) | [Français](docs/README.fr.md) | [Deutsch](docs/README.de.md) | [Português](docs/README.pt.md) | [Русский](docs/README.ru.md)

---

## Abstract

Every AI tool forgets you after every session. You close a window, and your preferences, decisions, and lessons vanish. Next session, you start from zero.

**Mem-Forever** is a Git-native memory layer that lets any AI agent remember you permanently. Memories are stored as compact I-Lang structures in your own private repo, readable by humans, parseable by machines, and portable across every tool.

Where context windows forget, **Mem-Forever endures**.

---

## Why

| | |
|---|---|
| **Persistent** | One memory, surviving every session and every model swap. |
| **Portable** | Plain-text I-Lang shards in `.ilang/`. `git diff`-able, no vendor lock-in. |
| **Automatic** | AI builds your profile from conversation. You never fill a form. |
| **Private** | Your repo, your data. No server, no account, no telemetry. |

---

## Quick Look

```
.ilang/
  soul.md      ← who you are (auto-generated from conversation)
  memory.md    ← what you decided, learned, built (auto-appended)
```

```ilang
::DNA{user}
::CORE{
  ::CONTEXT{role:fullstack_dev|experience:10yr}
  ::GENE{style|conf:confirmed}
    T:conclusions_first
    T:minimal_output|when:simple
    A:verbose_without_signal⇒waste
}
::LESSONS{
  ::LESSON{id:serverless_no_shared_state|conf:confirmed}
}
```

Every preference is **addressable**, **scoped**, **versioned**, and **falsifiable**.

---

## Setup (seconds)

**Step 1** &ensp; Click **"Use this template"** → **Create a new repository** → Set to **Private**.

**Step 2** &ensp; There is no step 2.

Open the repo with any AI tool. It reads the instruction files, asks you a few questions, builds your profile. From that point on, it remembers.

---

## Works With Everything

| Tool | Auto-reads | How |
|---|---|---|
| Claude Code | `CLAUDE.md` | Open repo, start working |
| Cursor | `.cursorrules` | Open repo, start working |
| Codex | `AGENTS.md` | Open repo, start working |
| Copilot | `.github/copilot-instructions.md` | Open repo, start working |
| Gemini CLI | `GEMINI.md` | Open repo, start working |
| ChatGPT | Project knowledge | Upload `soul.md` |
| Claude.ai | Project knowledge | Upload `soul.md` |
| Gemini web | Google Drive | Sync `soul.md` to Drive |

### Working on a different project?

One sentence restores full context:

> *My memory repo is at `https://github.com/YOU/mem-forever`. PAT: `ghp_xxx`. Clone it, read `.ilang/soul.md` and `.ilang/memory.md`, then come back here.*

### Multiple projects?

Use this template again. `mem-forever-work`, `mem-forever-research`, `mem-forever-client-x`. Each repo is an independent memory. Same engine, different context.

---

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  You talk    │────▶│  AI reads    │────▶│  AI updates  │
│  to any AI   │     │  .ilang/     │     │  .ilang/     │
│  tool        │     │  soul.md     │     │  memory.md   │
│              │     │  memory.md   │     │  soul.md     │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
                                          git commit
                                          git push
                                                │
                                         ┌──────▼──────┐
                                         │ Your private │
                                         │ GitHub repo  │
                                         └─────────────┘
```

**soul.md** is your behavioral profile. Built from conversation, sharpened every session through mutation and decay rules. Think of it as DNA that travels with you.

**memory.md** is your logbook. Decisions, lessons, facts, progress. Append-only. Git history preserves everything.

You never write these files. Your AI does. You can read, edit, or delete them anytime. They are yours.

---

## Comparison

| | Mem-Forever | Nowledge Mem | Mem0 |
|---|---|---|---|
| Install | Use template | Download app + configure | pip install + API key |
| Config | None | MCP + plugins + LLM | SDK integration |
| Storage | Your GitHub repo | Local SQLite | Cloud vectors |
| Cross-tool | Any tool that reads files | Plugin per tool | API per tool |
| Price | Free forever | Free / Pro | Free / Pro |
| Data ownership | You | You | Theirs |
| Migration | `git clone` | Export | API call |

---

## Under the Hood

The instruction files contain behavioral rules written in [I-Lang v4.0](https://ilang.ai), a structured protocol that AI models parse natively. These rules tell the AI how to extract preferences, format memories, handle conflicts, and evolve your profile over time.

You don't need to know I-Lang. You just talk to your AI, and it gets better at working with you.

---

## License

MIT

---

<sub>Built by <a href="https://ilang.ai">I-Lang Protocol</a> · The native language of artificial intelligence</sub>

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
> A persistent memory layer for AI agents, built on the iLang protocol. Version 2.0 turns the memory repo into a portable brain: a profile, one file per memory, a hand-off note that says where you stopped, and an encrypted vault for your keys.
>
> iLang is the first protocol to formally map Greek mathematical symbols (Σ, Δ, φ, λ, Ω, ∇, μ, Π, ψ, ξ, ζ, θ, ∂) as primitive verbs for AI-to-AI communication, and the first to define a computable vector space for AI judgment (11 dimensions, 4 axioms, fuzzy-mathematical foundation).

[![License](https://img.shields.io/badge/license-MIT-d4a858?style=flat-square)](LICENSE)
[![Protocol](https://img.shields.io/badge/protocol-iLang_v5.0-d4a858?style=flat-square)](https://ilang.ai)
[![iLang L0](https://img.shields.io/badge/iLang-L0_Compatible-d4a858?style=flat-square)](https://github.com/ilang-ai/ilang-spec)
[![Tools](https://img.shields.io/badge/works_with-Claude_·_Cursor_·_Codex_·_Copilot_·_Gemini-d4a858?style=flat-square)]()
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22865160.svg)](https://doi.org/10.5281/zenodo.22865160)

[中文](docs/README.zh.md) | [日本語](docs/README.ja.md) | [한국어](docs/README.ko.md) | [Español](docs/README.es.md) | [Français](docs/README.fr.md) | [Deutsch](docs/README.de.md) | [Português](docs/README.pt.md) | [Русский](docs/README.ru.md)

---

## Abstract

Every AI tool forgets you after every session. You close a window, and your preferences, decisions, and lessons vanish. Next session, you start from zero. Switch machines, and even the keys your agent needed are gone.

**Mem-Forever** is a Git-native memory layer that lets any AI agent remember you permanently. Memories are small Markdown files with [OKF](docs/OKF.md) frontmatter and iLang declarations in your own private repo: readable by humans, parseable by machines, portable across every tool. 2.0 adds the parts that let a new session, a new tool or a new machine pick up exactly where the last one stopped. 1.0 kept one long conversation going; 2.0 keeps the memory itself, and makes a hand-off between two models something you can audit: judgment before action, review before merge.

Where context windows forget, **Mem-Forever endures**.

---

## Why

| | |
|---|---|
| **Persistent** | One memory, surviving every session and every model swap. |
| **Portable** | Plain Markdown in `soul/`, `memory/`, `handoff/`. `git diff`-able, no vendor lock-in. |
| **Automatic** | AI builds your profile from conversation. You never fill a form. |
| **Private** | Your repo, your data. No server, no account, no telemetry. |
| **Resumable** | `handoff/CURRENT.md` says what was done, what is next and what is unverified. The next session, in any tool, starts there. |
| **Complete** | `vault/` carries your keys, age-encrypted. A fresh machine is thirty minutes from working. |

---

## Quick Look

```
BRAIN.md              ← read me first; also the text you paste into web chat tools
handoff/CURRENT.md    ← where you stopped: done / next / unverified
soul/soul.md          ← who you are (auto-generated from conversation)
memory/MEMORY.md      ← index, one line per memory
memory/*.md           ← one memory per file, with a `type` frontmatter
vault/keys-*.age      ← your keys, encrypted to your own public key
docs/PASTE.md         ← the third way in: a chat AI with no tools
tools/brain.py        ← optional: check, migrate, vault, install, handoff review, paste
```

```ilang
::STATE{@OWNER, kind:person, role:fullstack_dev, alias:the I in this chat}
::GENE{style|conf:confirmed|scope:global}
T:conclusions_first
T:minimal_output|when:simple
A:verbose_without_signal⇒waste
::FACT{key:preferred_stack|value:react, node|conf:confirmed}
```

```ilang
::STATE{@TASK, name:ship v1.2, repo:my-app, branch:main, owner:@OWNER}
::PROGRESS{date:2026-11-04|done:§1 tests green|next:tag and release|unverified:docs build}
::BOUNDARY{never:force-push main|scope:project}
```

Every preference is **addressable**, **scoped**, **versioned**, and **falsifiable**. Every hand-off is four fields any tool can read: date, done, next, unverified. The notation is the iLang canon; every template file passes its grammar validator with zero errors and zero warnings.

---

## Setup (seconds)

**Step 1** &ensp; Click **"Use this template"** → **Create a new repository** → Set to **Private**.

**Step 2** &ensp; There is no step 2.

Open the repo with any AI tool. It reads the instruction files, reads the hand-off, asks you a few questions, builds your profile. From that point on, it remembers.

**Optional accelerator.** `tools/brain.py` is one Python file, standard library only, Python 3.10+:

```
python -X utf8 tools/brain.py check        # frontmatter valid, no secret-like text, before every push
python -X utf8 tools/brain.py migrate-cc   # bring Claude Code's auto-memory files into memory/
python -X utf8 tools/brain.py vault pack   # encrypt your keys into vault/ (see docs/VAULT.md)
python -X utf8 tools/brain.py install      # wire this repo into Claude Code on this machine
python -X utf8 tools/brain.py paste        # one message for a chat AI with no tools: the card plus the hand-off (docs/PASTE.md)
python -X utf8 tools/brain.py handoff review returned.md   # compare a hand-off another model wrote with yours before merging
```

---

## Works With Everything

| Tool | Auto-reads | How |
|---|---|---|
| Claude Code | `CLAUDE.md` | Open repo, start working. `brain.py install` also links its auto-memory into `memory/`. |
| Cursor | `.cursorrules` | Open repo, start working |
| Codex | `AGENTS.md` | Open repo, start working |
| Copilot | `.github/copilot-instructions.md` | Open repo, start working |
| Gemini CLI | `GEMINI.md` | Open repo, start working |
| ChatGPT | Custom instructions + connector | Paste `BRAIN.md`; connect the repo (GitHub) or a Drive mirror |
| Claude.ai | Project instructions + connector | Paste `BRAIN.md`; connect the repo with the GitHub connector |
| Gemini web | Gem instructions + Drive | Paste `BRAIN.md`; mirror the repo to Drive |
| Any chat AI, no tools | One pasted message | `brain.py paste` builds it: the notation card plus the hand-off. It hands changes back as blocks in a code fence |

Web tools that cannot write git hand their changes back as blocks in a code fence; a tool that can write git runs `brain.py handoff review` on them and records what passes. `BRAIN.md` says so in about 400 tokens; [docs/PASTE.md](docs/PASTE.md) has the five questions that show whether a model read the notation or guessed.

### Working on a different project?

One sentence restores full context:

> *My brain repo is at `https://github.com/YOU/brain`. Read `BRAIN.md` there, then come back here.*

Give the agent access through its own connector (GitHub app, Drive) or a local clone. Never paste a token into a prompt; keys travel in `vault/`, see [docs/VAULT.md](docs/VAULT.md).

### Multiple projects?

Use this template again. `brain-work`, `brain-research`, `brain-client-x`. Each repo is an independent memory. Same engine, different context.

---

## What's new in 2.0

- **Layout.** `soul/` (profile), `memory/` (one file per memory plus an index), `handoff/` (where you stopped), `rules/`, `env/`, `vault/`, `tools/`. `.ilang/` is deprecated and kept for one version.
- **Hand-off at every milestone.** The skill updates `handoff/CURRENT.md` when something is deployed, configured or decided, not at session end. A session that reads `status: open` claims it; git is the lock.
- **OKF frontmatter.** Every file under `soul/`, `memory/`, `handoff/` carries a `type`. `brain.py check` enforces the three rules and scans for secret-like text. See [docs/OKF.md](docs/OKF.md).
- **Vault.** Keys, SSH private keys and the values behind `[REDACTED kind fingerprint]` markers in memory go into one [age](https://age-encryption.org)-encrypted bundle. The private key lives in your password manager and on paper. See [docs/VAULT.md](docs/VAULT.md).
- **Notation on the iLang canon.** `::STATE`, `::FACT{key|value|conf}`, `::PROGRESS{date|done|next|unverified}`, `::DECIDE{@X}{what|why|context}`, `::LESSON` plus one line of prose, `::BOUNDARY{never|scope}`. Every template file passes the canon grammar validator with zero errors and zero warnings. The quick card is 381 to 410 tokens on ten tokenizers (539 on Claude's); its three non-obvious rules come from running five check questions on twelve model tiers.
- **Judgment before action.** Reading, recapping or exporting the hand-off is not doing the work. A `next` item that crosses a boundary stops; missing evidence asks; the owner's call defers. A hand-off request authorizes nothing.
- **Review before merge.** A hand-off another model wrote is a candidate. `brain.py handoff review` compares it block by block with the accepted one and rejects a deleted boundary, a forbidden or unevidenced `done`, a missing key, an empty value, a changed identifier and a silent drop; the rest goes to you.
- **Paste.** `brain.py paste` builds the one message a chat AI with no tools needs; `docs/PASTE.md` has the five check questions and what was measured.
- **brain.py.** `check`, `migrate-cc`, `vault pack / unpack / verify`, `install`, `init`, `status`, `handoff open / claim / close / show / review`, `paste`, `export-drive`. One file, no dependencies.
- **No token in prompts.** Access goes through connectors or a clone.

## Coming from 1.0

Open your repo with any tool; the skill migrates once: `.ilang/soul.md` content moves to `soul/soul.md`, `.ilang/memory.md` is copied to `memory/memory-1.0.md` with a frontmatter and indexed, and the `.ilang/` files stay as pointers until 2.1. Then run `python -X utf8 tools/brain.py check`. Old block names (`::DECIDED`, `::LEARNED`, the `::DNA{}` / `::CORE{}` wrapper) are read as notes and rewritten only when a file is touched.

---

## How It Works

```
┌─────────────┐     ┌────────────────┐     ┌────────────────┐
│  You talk    │────▶│  AI reads      │────▶│  AI writes     │
│  to any AI   │     │  handoff/      │     │  memory/*.md   │
│  tool        │     │  soul/         │     │  handoff/      │
│              │     │  memory index  │     │  soul/         │
└─────────────┘     └────────────────┘     └───────┬────────┘
                                                   │
                                             git commit
                                             git push
                                                   │
                                            ┌──────▼──────┐
                                            │ Your private │
                                            │ GitHub repo  │
                                            │ + vault/     │
                                            └─────────────┘
```

**soul/soul.md** is your behavioral profile. Built from conversation, sharpened every session through mutation and decay rules. Think of it as DNA that travels with you.

**memory/** is your logbook, one fact per file. Decisions, lessons, facts, references. Append-only. Git history preserves everything.

**handoff/CURRENT.md** is the note you leave on the desk: date, done, next, unverified. The next session reads it first. A hand-off that comes back from another model is reviewed against it before it may replace it.

You never write these files. Your AI does. You can read, edit, or delete them anytime. They are yours.

---

## Comparison

| | Mem-Forever | Nowledge Mem | Mem0 |
|---|---|---|---|
| Install | Use template | Download app + configure | pip install + API key |
| Config | None | MCP + plugins + LLM | SDK integration |
| Storage | Your GitHub repo | Local SQLite | Cloud vectors |
| Cross-tool | Any tool that reads files | Plugin per tool | API per tool |
| Resume across sessions | `handoff/CURRENT.md` | Session history | Session history |
| Keys for a new machine | `vault/`, age-encrypted | n/a | n/a |
| Price | Free forever | Free / Pro | Free / Pro |
| Data ownership | You | You | Theirs |
| Migration | `git clone` | Export | API call |

---

## Under the Hood

The instruction files contain behavioral rules written in [iLang v5.0](https://ilang.ai), a structured protocol tested across ChatGPT, Claude, Gemini, DeepSeek, Kimi, Qwen and GLM. These rules tell the AI how to extract preferences, format memories, keep the hand-off current, handle conflicts, and evolve your profile over time. `rules/GRAMMAR-CARD.md` is the whole reading guide: nine rules, one screen, measured on ten tokenizers.

You don't need to know iLang. You just talk to your AI, and it gets better at working with you.

---

## Citation

[CITATION.cff](CITATION.cff); Zenodo archives each release. Concept DOI [10.5281/zenodo.22865160](https://doi.org/10.5281/zenodo.22865160) (all versions).

## License

MIT

---

<sub>Built by <a href="https://ilang.ai">iLang Protocol</a> · The native language of artificial intelligence</sub>

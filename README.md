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

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/banner-dark.svg">
  <img src="docs/assets/banner-light.svg" alt="Mem-Forever: memory that outlives the session. A ruler of sessions with the current one marked in gold." width="1200">
</picture>

> **永久记忆 · 跨会话 · 跨模型**
> A persistent memory layer for AI agents, built on the iLang protocol. One private Git repo is the agent's brain: a profile, one file per memory, a hand-off note that says where you stopped, and an encrypted vault for your keys. **2.1: this README is the engineering book. Copy it into any AI agent and the agent can carry it out.**
>
> iLang is the first protocol to formally map Greek mathematical symbols (Σ, Δ, φ, λ, Ω, ∇, μ, Π, ψ, ξ, ζ, θ, ∂) as primitive verbs for AI-to-AI communication, and the first to define a computable vector space for AI judgment (11 dimensions, 4 axioms, fuzzy-mathematical foundation).

[![License](https://img.shields.io/badge/license-MIT-d4a858?style=flat-square)](LICENSE)
[![Protocol](https://img.shields.io/badge/protocol-iLang_v5.0-d4a858?style=flat-square)](https://ilang.ai)
[![iLang L0](https://img.shields.io/badge/iLang-L0_Compatible-d4a858?style=flat-square)](https://github.com/ilang-ai/ilang-spec)
[![Tools](https://img.shields.io/badge/works_with-Claude_·_Cursor_·_Codex_·_Copilot_·_Gemini-d4a858?style=flat-square)]()
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22865160.svg)](https://doi.org/10.5281/zenodo.22865160)

Landing page: <https://ilang-ai.github.io/Mem-Forever/>

[中文](docs/README.zh.md) | [日本語](docs/README.ja.md) | [한국어](docs/README.ko.md) | [Español](docs/README.es.md) | [Français](docs/README.fr.md) | [Deutsch](docs/README.de.md) | [Português](docs/README.pt.md) | [Русский](docs/README.ru.md)

---

## Abstract

Every AI tool forgets you after every session. You close a window, and your preferences, decisions, and lessons vanish. Next session, you start from zero. Switch machines, and even the keys your agent needed are gone.

**Mem-Forever** is a Git-native memory layer that lets any AI agent remember you permanently. Memories are small Markdown files with [OKF](docs/OKF.md) frontmatter and iLang declarations in your own private repo: readable by humans, parseable by machines, portable across every tool. 1.0 kept one long conversation going. 2.0 keeps the memory itself, and makes a hand-off between two models something you can audit: judgment before action, review before merge. 2.1 makes this page the whole manual: what to paste, what to run, what the agent then does, and what was measured.

Where context windows forget, **Mem-Forever endures**.

| | |
|---|---|
| **Persistent** | One memory, surviving every session and every model swap. |
| **Portable** | Plain Markdown in `soul/`, `memory/`, `handoff/`. `git diff`-able, no vendor lock-in. |
| **Automatic** | AI builds your profile from conversation. You never fill a form. |
| **Private** | Your repo, your data. No server, no account, no telemetry. |
| **Resumable** | `handoff/CURRENT.md` says what was done, what is next and what is unverified. The next session, in any tool, starts there. |
| **Complete** | `vault/` carries your keys, age-encrypted. A fresh machine is thirty minutes from working. |

---

## How to read this page

Three kinds of reader open this page. Find yours; each block below is complete on its own and runs as it is.

| You are | Start at |
|---|---|
| A chat AI with no tools: a web chat, no files, no shell | **§1** — one message to read, one rule for writing back |
| An agent with a shell: Claude Code, Cursor, Codex, Copilot, Gemini CLI, Hermes, or a person at a terminal | **§2** — copy the block for your shell and run it |
| An agent that already has the repo open | **§3** — your instruction file is already in place |

Everything from §4 on is the protocol and the evidence. The normative text for agents is [`skills/mem-forever/SKILL.md`](skills/mem-forever/SKILL.md); the five instruction files (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, `.github/copilot-instructions.md`) mirror its body byte for byte.

---

## 1. No tools: the pasted message

A brain reaches a chat AI that has no tools as one pasted message: the notation card below, a `---` line, then the declaration blocks of the hand-off. `python -X utf8 tools/brain.py paste` builds that message from a brain, in the owner's language: this English card ships as [rules/GRAMMAR-CARD.md](rules/GRAMMAR-CARD.md), the Chinese one as `rules/GRAMMAR-CARD.zh.md`, and `--lang auto` picks by the hand-off. [docs/PASTE.md](docs/PASTE.md) has the one check to run before real work. The card, verbatim:

```
# iLang notation quick card (for reading a brain)

- `::NAME{k:v|k2:v2}` is one declaration block. NAME is upper case. Fields split on `|`, key and value on `:`.
- `::GENE{name|conf|scope}` is followed by `T:` lines (traits: I do it this way) and `A:x⇒y` lines (anti-patterns: x leads to y, don't).
- `conf:tentative|confirmed` confidence; `scope:global|project` scope; `when:condition` says when a block applies; it is not a release clause.
- `@NAME` in upper case is an entity: person, repo, machine, task.
- `::STATE{@X, k:v}` an entity's state now. `::FACT{key|value|conf}` a fact. `::PROGRESS{date|done|next|unverified}` progress.
  `::DECIDE{@X}{what|why|context}` a decision, X = who decided. `::LESSON{id|type|scope|conf}` plus the next line of prose = a lesson.
  `::BOUNDARY{never|scope}` a hard boundary: it always wins, no condition lifts it, never offer a way around it.
- How to read: take keys and values literally; no dictionary needed. An unknown block is a labelled note: read its body.
- Restating a hand-off: item by item, verbatim, keep the numbering, do not rephrase.
- Writing a block back: the whole block inside a triple-backtick fence; every key present, `none` for a key you have no material for; count the keys before sending.
- Never say DNA, gene or mutation to the user; say "I noted that" or "you told me last time".
```

**Writing back.** The chat AI returns the whole `::PROGRESS{date|done|next|unverified}` block (or a `::DECIDE{}`, a `::LESSON{}`) inside one code fence, every key present, `none` where there is no material. Items are identifiers: an item moves between `done`, `next` and `unverified` whole, and news or evidence goes in a new item. Say that sentence before you ask for the block; without it a model rewrites the item it moves, and the review in §4.4 rejects the rewrite. A tool that can write git takes the returned block through `brain.py handoff review --overlay` and records what passes.

---

## 2. A shell: bootstrap

Both blocks end in the same place: a private brain on your disk, checked, on branch `main`, ready to push to an empty private repository you create. Requirements: git and Python 3.10 or newer; nothing else. Run the block for your shell as it is.

PowerShell (Windows):

```powershell
git clone --depth 1 https://github.com/ilang-ai/Mem-Forever.git brain
Set-Location brain
Remove-Item -Recurse -Force .git
git init -q -b main
python -X utf8 tools/brain.py check
git add -A
git commit -q -m "init: brain from Mem-Forever 2.1"
# Then create an EMPTY PRIVATE repository on GitHub and run:
#   git remote add origin https://github.com/YOU/brain.git
#   git push -u origin main
```

bash (macOS, Linux):

```bash
git clone --depth 1 https://github.com/ilang-ai/Mem-Forever.git brain \
 && cd brain && rm -rf .git && git init -q -b main \
 && python3 -X utf8 tools/brain.py check \
 && git add -A && git commit -q -m "init: brain from Mem-Forever 2.1"
# Then create an EMPTY PRIVATE repository on GitHub and run:
#   git remote add origin https://github.com/YOU/brain.git && git push -u origin main
```

Acceptance: `check: 0 errors` on the last tool line, `git status` clean. Then open the folder with any tool in §3; it reads the hand-off, asks you a few questions, builds your profile. From that point on, it remembers.

**No shell at all?** Click **"Use this template"** on GitHub → **Create a new repository** → **Private**. Same result, one commit.

`tools/brain.py` is one Python file, standard library only. The commands you will meet:

```
python -X utf8 tools/brain.py check        # frontmatter valid, no secret-like text, before every push
python -X utf8 tools/brain.py migrate-cc   # bring Claude Code's auto-memory files into memory/
python -X utf8 tools/brain.py vault pack   # encrypt your keys into vault/ (see docs/VAULT.md)
python -X utf8 tools/brain.py install      # wire this repo into Claude Code on this machine
python -X utf8 tools/brain.py paste        # the one message for a chat AI with no tools (§1)
python -X utf8 tools/brain.py handoff review returned.md --overlay --out candidate.md   # review a write-back (§4.4)
```

---

## 3. The repo open: which file your tool reads

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
| Any chat AI, no tools | One pasted message | §1: the card plus the hand-off; it writes back blocks in a code fence |

`BRAIN.md` is the eight-point entry a chat AI with a connector reads first; it is kept under about 400 tokens on the receiving model's tokenizer (§5).

**Working on a different project?** One sentence restores full context: *"My brain repo is at `https://github.com/YOU/brain`. Read `BRAIN.md` there, then come back here."* Give the agent access through its own connector (GitHub app, Drive) or a local clone. Never paste a token into a prompt; keys travel in `vault/`, see [docs/VAULT.md](docs/VAULT.md).

**Multiple projects?** Use the template again: `brain-work`, `brain-research`, `brain-client-x`. Each repo is an independent memory. Same engine, different context.

---

## 4. The protocol

### 4.1 Layout

```
BRAIN.md              ← read me first; also the text you paste into web chat tools
handoff/CURRENT.md    ← where you stopped: done / next / unverified
soul/soul.md          ← who you are (auto-generated from conversation)
soul/agent.md         ← the agent's own soul: a persona you gave it, and what it learned with you
memory/MEMORY.md      ← index, one line per memory
memory/*.md           ← one memory per file, with a `type` frontmatter
vault/keys-*.age      ← your keys, encrypted to your own public key
rules/GRAMMAR-CARD.md ← the notation card of §1 (English; GRAMMAR-CARD.zh.md in Chinese)
docs/PASTE.md         ← the third way in: a chat AI with no tools
tools/brain.py        ← optional: check, migrate, vault, install, init, handoff review, paste
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
::PROGRESS{date:2026-11-05|done:§1 tests green|next:tag and release|unverified:docs build}
::BOUNDARY{never:force-push main|scope:project}
```

Every preference is **addressable**, **scoped**, **versioned**, and **falsifiable**. Every hand-off is four fields any tool can read: date, done, next, unverified. The notation is the iLang canon; every template file passes its grammar validator with zero errors and zero warnings.

### 4.2 Session start

1. Read `handoff/CURRENT.md`. Tell the user in two sentences what was done, what comes next and what is unverified. If `status: open`, claim it: append yourself to `claimed_by`, set `status: claimed`, commit.
2. Check `soul/`, `memory/`, `handoff/`, `log.md` for uncommitted changes; commit and push them. They are unsaved memories from a previous session.
3. Read `soul/soul.md`; if it is still the template, run onboarding: one question per message, role, work style, one clear preference, then write the file. Read `soul/dna.md` if it has content. Read `soul/agent.md`: part one is a persona the owner gave the agent, part two is what it learned with this owner.
4. Read `memory/MEMORY.md`, the index. Open a file under `memory/` only when the task needs it.
5. Do what the user asks, with the preferences from `soul/` applied.

### 4.3 Judgment before action

Reading the hand-off, restating it, updating it or exporting it is recording, not doing. Each item under `next` is judged on its own before anything happens:

- It conflicts with a `::BOUNDARY{}`: that action stops. The item and the reason stay in `next` or `unverified`; it never enters `done`.
- The evidence an action or a completion claim needs is missing: ask one question, record what is missing under `unverified`. No invented evidence, no accepted claim.
- It is the owner's call, or nobody authorized it: defer, record the pending decision, do not execute.
- Otherwise it proceeds only when the owner asked for it or already authorized it. A request to check, recap or hand off authorizes nothing.

### 4.4 Hand-off and review

A milestone is a deploy that succeeded, a config that changed, a conclusion that was reached, and any moment before the session might be cut off. At each one the agent updates `::PROGRESS{date|done|next|unverified}` in `handoff/CURRENT.md` and commits; it does not wait for the session to end. An item enters `done` only with evidence from the conversation or an observed result, and it keeps its text. When the task is done the file is closed and archived under `handoff/archive/`, and a fresh `CURRENT.md` is opened in the same commit.

A hand-off that comes back from another model or another session is a candidate, not the truth. `python -X utf8 tools/brain.py handoff review <candidate>` compares it block by block with the accepted one and never writes:

- **Rejected**, baseline stays (exit 1): a boundary deleted, weakened, rewritten or given a `when:`; an item in `done` that a boundary forbids; a missing key or an empty value; a changed identifier; an item of `next` or `unverified` dropped without a word; a secret-like string.
- **For the owner** (exit 3): a `next` item that moved to `done` (evidence needed), a new `done` item, a fact whose value changed, a confidence raised, a decision whose reason changed.
- **Clean** (exit 0): identical, or only additions.

`--validator <path to ilang_grammar_validator.py>` runs the canon grammar check on the candidate as well. `--overlay` is for a candidate that holds only the blocks it changed, which is what a web chat sends back: the tool lays those blocks over the baseline by identifier, carries the rest of the baseline in, and reviews the whole; `--out <file>` writes that whole. Accepting is saving the accepted whole as `CURRENT.md` and committing `handoff: accept from <who>`; the previous version stays in git history. Grammar success is not truth: the key count is only a completeness check, and evidence is a recorded owner statement or an observed tool result.

### 4.5 Memory, soul, vault

- **One memory is one file** under `memory/`, with a `type` frontmatter (`user`, `feedback`, `project`, `reference`) and one index line in `memory/MEMORY.md`. Append or merge, never overwrite; patterns, not events; absolute dates; 200 lines per file, then fold the oldest into a summary paragraph. Every change is its own commit, pushed at once.
- **`soul/soul.md`** is the owner's profile: `::STATE{@OWNER…}`, one `::GENE{}` per area with `T:` traits and `A:` anti-patterns, `::FACT{}` lines, `::BOUNDARY{}` lines. A behavior seen three times becomes `confirmed`; an explicit rejection becomes an `A:` line; a tentative trait unseen for 30 days goes; two traits that contradict split by a `when:` condition. Boundaries never split and never carry `when:`.
- **`soul/agent.md`** is the agent's own soul, new in 2.1: a persona block the owner gave it, kept verbatim with its version and hash in the frontmatter, and below it what the agent learned with this owner, in `::LESSON{}` and `::GENE{}` blocks it writes at milestones. It never overrides `soul/soul.md` or a boundary.
- **Secrets never enter a text file.** The memory says `[REDACTED <kind> <fingerprint>]`; the value goes into one [age](https://age-encryption.org)-encrypted bundle under `vault/`, whose private key lives in your password manager and on paper. `brain.py check` scans every push for secret-like strings. See [docs/VAULT.md](docs/VAULT.md).
- **Transparency.** The agent never says "DNA", "gene", "mutation" or "decay" to the user; it says "I saved some notes" or "I remember from last time". The owner can read, edit or delete any file at any time.

### 4.6 Acceptance checks

A brain, or a change to this template, is in order when all of these hold:

1. `python -X utf8 tools/brain.py check` reports 0 errors and 0 secret-like hits.
2. The canon grammar validator (`ilang_grammar_validator.py --lint <file> --strict`, from [ilang-spec](https://github.com/ilang-ai/ilang-spec)) reports 0 errors and 0 warnings on every Markdown file that carries blocks.
3. `BRAIN.md` and the card each stay near 400 tokens on the receiving model's own tokenizer; measure, do not estimate (§5).
4. The five instruction files are byte-identical to the body of `skills/mem-forever/SKILL.md`.
5. A returned hand-off goes through `handoff review` before it replaces `CURRENT.md`, and the commit says whom it was accepted from.

---

## 5. Measured

Numbers are from real tokenizers and real conversations, not estimates; dates are when they were taken.

- **The card** ([rules/GRAMMAR-CARD.md](rules/GRAMMAR-CARD.md), English, 1351 bytes): 381 to 410 tokens on ten models' tokenizers (MiniMax, Grok 4.20 and 4.7, GLM, Kimi, DeepSeek, Qwen, Gemini, GPT, Doubao), 539 on Claude's. Measured 2026-11-04; not yet tested in conversation.
- **The Chinese card** (`rules/GRAMMAR-CARD.zh.md`, 1212 bytes): 352 to 392 tokens on the same ten, 542 on Claude's. Tested in conversation on twelve model tiers from weak to strong, 2026-11-03 and 2026-11-04.
- **`BRAIN.md`** (the eight points, English): 1552 bytes; 399 to 406 tokens on GPT, GLM and Kimi, 427 on Doubao, 588 on Claude's, net of each chat template, measured 2026-11-05 after the 2.1 edit of point 2.
- **One web endpoint, 2026-11-05**, ChatGPT's web chat signed out, free tier, no files, no tools: the Chinese card plus a 14-block hand-off went in as one message and came back as "done reading"; the restating check gave 4, 6 and 9 items verbatim, confirmed by script against the file. The first write-back rewrote the item it moved and the review rejected it (two rejects); told the identifier rule, the second write-back passed (one flag, one transition, one addition) and was accepted.
- **`handoff review` self-test**, 2026-11-05: `init` into an empty directory, then `check`: 0 errors, and the seven generated files are validator-clean. An identical candidate: clean, exit 0. A single `::PROGRESS{}` block without `--overlay`: 13 rejects (every other baseline block reported missing), exit 1. The same block with `--overlay`: 0 rejects, 1 flag, 1 transition, 1 addition, exit 3, and the composed file equals the hand-made overlay from the web-endpoint run. A boundary given a `when:` under `--overlay`: rejected. One new `::LESSON{}` with its body line under `--overlay`: appended intact before the notes section, exit 0. A `::GENE{}` replaced under `--overlay` keeps its `T:`/`A:` lines, their indentation and the baseline's line endings.

---

## 6. Versions

### What's new in 2.1

- **This page is the engineering book.** Three readers, three entry blocks, each runs as it is; the protocol and the measurements follow. The translations keep the first screen and point here.
- **Partial write-back.** `handoff review --overlay` lays the blocks a web chat sent back over the baseline and reviews the whole; `--out` writes it. Accepting no longer copies the previous version into `handoff/archive/`; git history is the previous version, and `archive/` holds closed hand-offs only.
- **Items are identifiers.** The skill, `BRAIN.md`'s companion text and [docs/PASTE.md](docs/PASTE.md) say it before a write-back is requested: an item moves whole, news goes in a new item. The card itself is unchanged and still measured as published.
- **`soul/agent.md`.** The agent's own soul file, created by `brain.py init`, read at session start, written by the agent at milestones.
- **The card in the owner's language.** English and Chinese ship; `brain.py paste` picks by the hand-off's language, `init` writes both.
- **brain.py 1.5**, standard library only.

### What's new in 2.0

- **Layout.** `soul/`, `memory/`, `handoff/`, `rules/`, `env/`, `vault/`, `tools/`; `.ilang/` deprecated.
- **Hand-off at every milestone**, claimed by the session that reads `status: open`; git is the lock.
- **OKF frontmatter** on every file under `soul/`, `memory/`, `handoff/`; `brain.py check` enforces it and scans for secret-like text ([docs/OKF.md](docs/OKF.md)).
- **Vault.** Keys, SSH private keys and redacted values in one age-encrypted bundle ([docs/VAULT.md](docs/VAULT.md)).
- **Notation on the iLang canon**, every template file validator-clean.
- **Judgment before action**, **review before merge**, **paste** for a chat AI with no tools.
- **No token in prompts.** Access goes through connectors or a clone.

### Coming from 1.0

Open your repo with any tool; the skill migrates once: `.ilang/soul.md` content moves to `soul/soul.md`, `.ilang/memory.md` is copied to `memory/memory-1.0.md` with a frontmatter and indexed, and the `.ilang/` files stay as pointers. Then run `python -X utf8 tools/brain.py check`. Old block names (`::DECIDED`, `::LEARNED`, the `::DNA{}` / `::CORE{}` wrapper) are read as notes and rewritten only when a file is touched.

### Known limits, next

- A reworded item is still a drop plus an addition to the review; an "item supersedes item" relation, or prefix matching, would let "the same item plus evidence" be recognized. Until then the identifier rule above is the workaround.
- The identifier rule is not on the card. Putting it there means re-measuring and re-testing the card on the ten tokenizers and twelve tiers.
- The English card is measured but not yet tested in conversation; the Chinese card it mirrors is.
- `data/ilang-memory-protocol.jsonl` still carries 1.0-era samples.

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

You never write these files. Your AI does. You can read, edit, or delete them anytime. They are yours.

---

## Comparison

| | Mem-Forever | Nowledge Mem | Mem0 |
|---|---|---|---|
| Install | Use template, or one shell block | Download app + configure | pip install + API key |
| Config | None | MCP + plugins + LLM | SDK integration |
| Storage | Your GitHub repo | Local SQLite | Cloud vectors |
| Cross-tool | Any tool that reads files, or one pasted message | Plugin per tool | API per tool |
| Resume across sessions | `handoff/CURRENT.md` | Session history | Session history |
| Keys for a new machine | `vault/`, age-encrypted | n/a | n/a |
| Price | Free forever | Free / Pro | Free / Pro |
| Data ownership | You | You | Theirs |
| Migration | `git clone` | Export | API call |

---

## Under the Hood

The instruction files contain behavioral rules written in [iLang v5.0](https://ilang.ai), a structured protocol tested across ChatGPT, Claude, Gemini, DeepSeek, Kimi, Qwen and GLM. These rules tell the AI how to extract preferences, format memories, keep the hand-off current, judge before acting, review before merging, and evolve your profile over time. `rules/GRAMMAR-CARD.md` is the whole reading guide: nine rules, one screen, measured on ten tokenizers.

You don't need to know iLang. You just talk to your AI, and it gets better at working with you.

---

## Citation

[CITATION.cff](CITATION.cff); Zenodo archives each release. Concept DOI [10.5281/zenodo.22865160](https://doi.org/10.5281/zenodo.22865160) (all versions).

## License

MIT

---

<sub>Built by <a href="https://ilang.ai">iLang Protocol</a> · The native language of artificial intelligence</sub>

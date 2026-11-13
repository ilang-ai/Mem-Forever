# Mem-Forever for Hermes Agent

Every AI tool forgets you after every session. This one doesn't. Your private Git repository is the agent's brain, and this plugin makes it Hermes's memory provider: the same repository Claude Code, Codex, Cursor, Copilot, Gemini CLI and a pasted chat already read.

The brain is a fork of [ilang-ai/Mem-Forever](https://github.com/ilang-ai/Mem-Forever): `BRAIN.md` is the entry, `handoff/CURRENT.md` says where you stopped, `soul/` is who you are, `memory/` is one file per memory, `log/` keeps your words verbatim, `env/ledger.env` is the ledger of the doors the brain can open. Everything is addressable iLang notation that any model reads literally; the protocol itself is in the repository's [README](https://github.com/ilang-ai/Mem-Forever#readme).

## Install

```bash
hermes plugins install mem-forever
hermes memory setup            # pick "mem-forever", give the path of your brain repository
```

The path is a clone of your private fork of the template (`<hermes_home>/mem-forever/brain` when left empty). Give a `remote` git URL instead and the plugin clones it on first use, with whatever git credentials this machine already has. No brain yet? Fork the template, clone it, run `python -X utf8 tools/brain.py init .` once, as the template README says.

Without the wizard:

```bash
hermes config set memory.provider mem-forever
hermes config set memory.mem-forever.repo /path/to/your/brain
```

Hermes keeps one external memory provider active at a time; selecting this one replaces the other provider, not the built-in `MEMORY.md`.

## What it does, and when

| Moment | What happens |
|---|---|
| Session start | Commits what a previous session left unsaved under `soul/ memory/ handoff/ log/`, pulls the brain from its remote, and puts `BRAIN.md` in the system prompt. |
| First turn | Hands the model `handoff/CURRENT.md`, `soul/soul.md`, `soul/agent.md` and the index `memory/MEMORY.md`. A file under `memory/` is opened by the model only when the task needs it. Later turns get `CURRENT.md` again only if it changed on disk. |
| Each turn | Appends your message to `log/YYYY-MM-DD.md` through `tools/brain.py log owner`, in the background, verbatim. The assistant's words are not logged. |
| A write through Hermes's built-in memory tool | Leaves a trace in the brain's log, so nothing is remembered in one place only. |
| Before compression | Commits and pushes the four directories, and hands the `::PROGRESS{date\|done\|next\|unverified}` line to the summary so the hand-off survives. |
| Session end | Commits and pushes the four directories. |
| Subagent or cron run | Reads the brain, never writes to it. |

One tool, `mem_forever`, runs the engine that ships inside the brain (`tools/brain.py`):

| Action | What it runs |
|---|---|
| `status` | HEAD, remote, unsaved files, the `::PROGRESS` line, `brain.py status --json` |
| `check` | `brain.py check`: layout, grammar, secret-like strings; 0 errors expected |
| `ledger_verify` | `brain.py ledger verify <row|all>`: which doors open today |
| `unlock` | `brain.py unlock <door>`: prints one ledger row into the context, only when a `next` item names its door and this machine holds the owner's grant; a top door also needs the owner's one-time code |
| `handoff_review` | `brain.py handoff review <candidate>`: a hand-off another model wrote is compared block by block with `CURRENT.md` before it may replace it (clean, rejected, or for the owner) |
| `recognize` | `brain.py recognize --json`: the owner's recent words against the soul anchors |
| `log` | `brain.py log agent --kind <kind>`: the agent's own decision or lesson, dated |
| `commit` | commits and pushes `soul/ memory/ handoff/ log/`; do it at every milestone |
| `pull` | `git pull --rebase` from the brain's remote |

Memories, the soul and the hand-off are edited with Hermes's normal file tools, as the protocol says: one memory per file with a `type` frontmatter, one index line, `::PROGRESS` updated at every milestone, not at session end. The plugin never rewrites a memory on its own.

The protocol is also available as a read-only skill, `mem-forever:mem-forever`, while this provider is active.

## Configuration

| Key | Meaning |
|---|---|
| `memory.provider` | `mem-forever` activates this provider |
| `memory.mem-forever.repo` | Path of the brain repository; empty means `<hermes_home>/mem-forever/brain` |
| `memory.mem-forever.remote` | Git URL cloned into that path when the path does not exist yet; optional |

No API key, no token, no environment variable. The plugin reads nothing from `.env`.

## What to know before you install

- **Shell commands.** The plugin runs `git` and `python -X utf8 tools/brain.py` inside your brain repository: `git status`, `add`, `commit`, `pull --rebase`, `push`, and `clone` once if you gave a remote. Commits use the git identity configured on this machine; if none is set, the commit fails and the files stay unsaved on disk until you set one.
- **Network.** The only network traffic is git to the remote of your own brain repository. No service of ours or anyone else's is called. Prompts and transcripts are not sent anywhere by this plugin.
- **What is written where.** Your messages, as Hermes hands them to memory providers (secrets already redacted by Hermes), are appended verbatim to `log/` in your private repository. In a shared gateway chat the user side of a turn can be someone else's words; messages flagged as a bot's are skipped, others are not told apart.
- **Keys.** The plugin stores no credentials and asks Hermes for none. The brain's ledger lives in your private repository, encoded at rest (reversible, not encryption, by design: a key is replaceable, a lockout is not). The `unlock` action prints one ledger row into the model's context, and only when the engine's own rules allow it: the door is named by a `next` item, this machine holds the owner's grant (`brain.py grant`), and a top door has the owner's one-time code. Nothing is printed otherwise.
- **Reads outside the plugin's own directory.** The brain repository, at the path you configure.
- **Single provider.** Hermes allows one external memory provider; `hermes memory setup` switches.
- **Platform.** Tested on Linux and Windows with git on PATH and the Python that runs Hermes (the engine is standard library only).

## Source and support

The plugin is the `hermes/` directory of [ilang-ai/Mem-Forever](https://github.com/ilang-ai/Mem-Forever), MIT, version-locked to the template (`3.2.0`). Issues: [ilang-ai/Mem-Forever/issues](https://github.com/ilang-ai/Mem-Forever/issues). Contact: contact@ilang.ai.

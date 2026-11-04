# OKF: the frontmatter every brain file carries

Mem-Forever 2.0 files under `soul/`, `memory/` and `handoff/` start with a YAML frontmatter that follows the [Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format) v0.2. OKF is deliberately small: one required key, a few optional ones, two reserved file names, and the rule that readers tolerate what they do not know. That is all `tools/brain.py check` enforces.

## The three rules `check` enforces

1. Every `.md` under `soul/`, `memory/` and `handoff/` has a frontmatter that parses (`---` on the first line, a closing `---`, `key: value` lines, two-space nesting, lists with `- `). `memory/MEMORY.md` is exempt: it is the index Claude Code reads natively and stays plain.
2. The frontmatter has a non-empty `type`.
3. The two reserved files are well formed: `index.md` at the repo root carries `okf_version: "0.2"`; `log.md` has `## YYYY-MM-DD` headings, newest first, real dates.

`check` also scans every text file for secret-like strings (token prefixes of common vendors, private key blocks, JWTs, bearer headers, passwords in URLs, `password:`-style lines, hex strings next to words like secret or token) and warns when `BRAIN.md` or `rules/GRAMMAR-CARD.md` grow past a byte budget. Exit code 1 means fix before pushing.

## Keys

| Key | Required | Meaning |
|---|---|---|
| `type` | yes | What kind of knowledge this is. Free text; see the types below. |
| `name` | no | Short slug. Claude Code memory files already have it. |
| `description` | no | One line. The index shows it. |
| `tags` | no | List of strings. |
| `status` | no | `stable` (default), `template`, `draft`, `deprecated`. The onboarding rule keys off `template`. |
| `stale_after` | no | A date after which the fact should be re-checked (certificates, domains, subscriptions). |
| `verified` | no | Date of the last check. |
| `generated` | no | `by` (which tool wrote it) and `at` (RFC 3339 with offset). `migrate-cc` fills both. |

Unknown keys are allowed and preserved. Claude Code's own `metadata:` block, for example, stays untouched next to the OKF keys.

## Types used in this template

| `type` | Where | Meaning |
|---|---|---|
| `profile` | `soul/soul.md`, `soul/dna.md` | Who the user is and how they work. |
| `user` | `memory/` | Facts about the user: role, expertise, preferences. |
| `feedback` | `memory/` | Guidance the user gave on how the agent should work, with the why. |
| `project` | `memory/` | Ongoing work, decisions, constraints. |
| `reference` | `memory/` | Pointers to external things: URLs, tickets, dashboards. |
| `handoff` | `handoff/CURRENT.md` | The active hand-off note; `status: open / claimed / closed`. |

OKF does not register types centrally. A reader that meets an unknown type treats the file as a generic note.

## Reserved files

`index.md`, at the root, is the bundle index. The minimum is:

```
---
okf_version: "0.2"
---
```

`log.md` is the change log for the bundle itself: layout, rules, tools. Not memories, not progress.

```
## 2026-11-03

- Repository created from the Mem-Forever 2.0 template.
```

## Examples

A memory file:

```
---
type: feedback
name: short-answers-first
description: Lead with the answer; the user reads the reasoning only when asked.
---
**Why:** three times the user cut a long explanation short and asked for the conclusion.
**How to apply:** first sentence is the answer; details after, only if useful.
```

A hand-off note, body in iLang declaration blocks (see `rules/GRAMMAR-CARD.md`):

```
---
type: handoff
name: handoff-current
project: my-app
opened: 2026-11-03T09:00:00+00:00
agent: claude-code
status: open
claimed_by: []
---
::STATE{@OWNER, kind:person, role:owner, alias:the I in this chat}
::STATE{@TASK, name:ship v1.2, repo:my-app, branch:main, owner:@OWNER}
::PROGRESS{date:2026-11-04|done:§1 tests green|next:tag and release|unverified:docs build}
```

## Coming from Claude Code's auto-memory

`python -X utf8 tools/brain.py migrate-cc <dir>` copies `~/.claude/projects/<slug>/memory/*.md` into `memory/` and adds what OKF needs without touching anything else:

| Claude Code key | OKF key | Handling |
|---|---|---|
| `name`, `description` | same | kept verbatim |
| `metadata.type` | top-level `type` | value copied; the `metadata:` block stays |
| (none) | `generated.by`, `generated.at` | tool name and the source file's mtime |
| `MEMORY.md` | not an OKF file | copied verbatim; `check` skips it |

The source directory is never modified. A file with no frontmatter is copied as is and reported, so you can decide.

## Coming from Mem-Forever 1.0

`.ilang/soul.md` becomes `soul/soul.md` with a `type: profile` frontmatter. `.ilang/memory.md` becomes `memory/memory-1.0.md` with a `type: reference` frontmatter and one line in `memory/MEMORY.md`. The skill does this once; the old files stay as pointers for one version.

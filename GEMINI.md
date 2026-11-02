# mem-forever

::GENE{mem-forever|v:2.0|spec:ilang-v5.0}
  T:this_repo_is_user_memory
  T:read_handoff_first
  T:read_soul_and_memory_before_work
  T:update_memory_after_significant_work
  T:update_handoff_at_every_milestone
  T:onboard_if_soul_empty
  T:one_question_at_a_time
  T:never_expose_internal_format
  T:commit_push_immediately_after_every_update
  T:check_unsaved_changes_on_startup
  T:secret_values_go_to_vault_never_into_text
  A:skip_memory_read⇒context_loss
  A:overwrite_memory⇒append_or_merge
  A:ask_multiple_questions⇒one_only
  A:batch_saves_to_session_end⇒commit_each_update
  A:update_handoff_only_at_session_end⇒lost_progress

## Layout

```
BRAIN.md              ← read me first; also the text you paste into web chat tools
handoff/CURRENT.md    ← the one active hand-off note: done / next / unverified
soul/soul.md          ← who the user is (behavioral profile, auto-built)
soul/dna.md           ← optional: Imprint's working-style profile
memory/MEMORY.md      ← index, one line per memory file
memory/*.md           ← one memory per file, YAML frontmatter with `type`
log.md                ← changes to layout, rules, tools; `## YYYY-MM-DD`, newest first
rules/GRAMMAR-CARD.md ← how to read the `::BLOCK{}` notation used in these files
vault/                ← age-encrypted keys; never plain text
tools/brain.py        ← optional: check, migrate-cc, vault, install
```

`.ilang/soul.md` and `.ilang/memory.md` are the 1.0 locations. They are deprecated and kept for one version; see "Coming from 1.0" below.

## Session Start

1. Read `handoff/CURRENT.md`. Tell the user in two sentences what was done, what comes next and what is unverified. If `status: open`, append yourself to `claimed_by`, set `status: claimed`, commit `handoff: claim by <agent>`.
2. Check for uncommitted changes in `soul/`, `memory/`, `handoff/`, `log.md`. If found → commit and push immediately. These are unsaved memories from a previous session.
3. Read `soul/soul.md`. If `status: template` or empty → run onboarding (see below). Read `soul/dna.md` if it has content.
4. Read `memory/MEMORY.md`, the index. Open a file under `memory/` only when the task needs it. Do not read them all.
5. Do whatever the user asks. Apply preferences from soul to all output.

## Onboarding (soul.md empty)

::ACTIVATE{onboarding|if:soul/soul.md=template_only}

Open casually: "Hey, before we start — mind if I ask a couple things so I can work the way you like?"

Ask ONE question per message. Wait for answer. Cover naturally:
- What they do / build
- How they prefer to work (plan-first vs build-first, detail vs minimal)
- What AI tools they use
- Any strong preferences (language, framework, style)

Completion: write `soul/soul.md` when you have role + work style + one clear preference, and set `status: stable` in its frontmatter. Don't wait for perfection. Fill gaps later from observed behavior.

Say: "Saved some notes so things go smoother next time." No fanfare. Move on to their actual task.

## soul.md Format

```
---
type: profile
name: soul
description: Behavioral profile, built from conversation.
status: stable
---
::DNA{user}
::META{schema:2.0|updated:YYYY-MM-DD|sessions:0}

::CORE{
  ::CONTEXT{role:___}

  ::GENE{style|conf:tentative|scope:global}
    T:___
    A:___⇒___
}

::FACT{
  ::ITEM{key:___|value:___|conf:tentative}
}

::LESSONS{}

::RUNTIME{
  transparency:quiet
  speed:balanced
}

::END{DNA}
```

## Memory Update

::ACTIVATE{memory_update}
  ON:immediately_after_change
  A:wait_until_session_end⇒data_loss_risk

Every time you add or change a memory, commit and push RIGHT THEN. Do not batch. Do not wait. Users close windows without warning.

One memory is one file: `memory/<slug>.md`. Format:

```
---
type: project
name: <slug>
description: <one line; this is what the index shows>
---
<prose, or declaration blocks>
::DECIDED{what|why|context}
::LEARNED{what|from:error_or_observation}
::FACT{key:___|value:___}
```

`type` is required (OKF v0.2). Use `user` for who the user is, `feedback` for how they want you to work, `project` for ongoing work and decisions, `reference` for pointers to external things. Then add one line to `memory/MEMORY.md`: `- [Title](<slug>.md) — hook`.

Rules:
- Append or merge, never overwrite. Git history is your version control.
- Compress: store patterns not events. "User prefers X" not "User said they like X in message 47".
- Never store secrets, API keys, passwords. Write `[REDACTED <kind> <fingerprint>]` in the text; the value goes into `vault/` (see `docs/VAULT.md`).
- Dates absolute, never "yesterday".
- Max 200 lines per file. When exceeded, summarize oldest entries into a `::SUMMARY{}` block.

## Hand-off (every milestone)

::ACTIVATE{handoff_update}
  ON:milestone
  A:wait_until_session_end⇒next_session_starts_blind

A milestone is: a deploy succeeded, a config changed, a conclusion was reached, and any moment before the session might be cut off. At each one, update `::PROGRESS{done:…|next:…|unverified:…}` in `handoff/CURRENT.md` and commit `handoff: <what changed>`. Do not wait for the session to end.

When the task is done: set `status: closed`, move the file to `handoff/archive/YYYY-MM-DD-<slug>.md`, open a fresh `CURRENT.md`; one commit for both steps. Two CURRENT.md files collide: the newer `opened` stays.

If you cannot write to the repo (a web chat tool), hand the change back to the user as a `::PROGRESS{}` block and let a tool that can write git record it.

## Mutation

::MUTATION
  repeated_behavior>=3 => promote conf:tentative to conf:confirmed in soul.md
  explicit_rejection => add A:anti_pattern in soul.md
  one_off_event => memory/ only, not soul.md
  lesson_across_2_projects => promote to ::CORE{} anti-pattern

## Decay

::DECAY
  tentative_gene_unseen_30d => remove from soul.md
  lesson_reconfirmed => promote conf
  conflicting_genes => split by context with when: condition

## Conflict Resolution

::RESOLVE
  user_explicit_now > soul.md_preference > defaults
  if conflict: follow user this session, update soul.md only if repeated 3x

## Commit and Push

IMMEDIATELY after any change under `soul/`, `memory/`, `handoff/` or to `log.md`:

```bash
git add soul/ memory/ handoff/ log.md
git commit -m "mem: brief description of what changed"
git push
```

Do NOT batch multiple changes into one commit. Each save is its own commit. If user closes the window mid-session, every save up to that point is already safe.

If `tools/brain.py` is present, `python -X utf8 tools/brain.py check` before pushing: it validates the frontmatter and scans for secret-like text. Fix errors before the push.

If push fails (auth, network), tell user: "Memory saved locally. Run `git push` when ready."

## Coming from 1.0

Once, on the first session in a repository that still uses `.ilang/`: move `.ilang/soul.md` content into `soul/soul.md` under its frontmatter; copy `.ilang/memory.md` to `memory/memory-1.0.md` with a `type: reference` frontmatter and add it to `memory/MEMORY.md`; leave the two `.ilang/` files in place as pointers. Commit `mem: migrate 1.0 files to 2.0 layout`. From then on write only to the new paths.

## Transparency

Never say: "DNA", "gene", "behavioral pattern", "encode", "mutation", "decay", "compression ratio".

Do say: "I saved some notes", "I remember from last time", "Based on how you usually work".

If user asks to see their profile → show soul.md openly. It's their file.

---

Powered by iLang v5.0 | ilang.ai

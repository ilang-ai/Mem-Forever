---
type: handoff
name: handoff-current
description: The one active hand-off note. A session that reads status: open claims it first.
project: global
opened: 2026-11-04T00:00:00+00:00
agent: template
status: open
claimed_by: []
generated:
  by: mem-forever/2.0
  at: 2026-11-04T00:00:00+00:00
---

::STATE{@OWNER, kind:person, role:owner, alias:the I in this chat}
::STATE{@TASK, name:<one-line task>, repo:<repo>, branch:<branch>, cwd:<working directory>, owner:@OWNER}
::PROGRESS{date:<YYYY-MM-DD>|done:§<section> <finished, listed by milestone>|next:<the first thing to do next>|unverified:<claimed done but not tested>}
::FACT{key:where_files_are|value:<paths of deliverables, scripts, logs>|conf:confirmed}
::FACT{key:blockers|value:<what is stuck and who decides>|conf:confirmed}
::DECIDE{@OWNER}{what:<what was settled this round>|why:<why, or none>|context:<the block above it rests on, or none>}
::LESSON{id:<key>|type:<kind>|scope:project|conf:tentative}
<the lesson in one line. Source: where it came from>

## Claim and close

- A new session that reads `status: open`: append yourself to `claimed_by`, set `status: claimed`, commit `handoff: claim by <agent>`.
- When the task is done: set `status: closed`, move the whole file to `handoff/archive/YYYY-MM-DD-<slug>.md`, open a fresh CURRENT.md; one commit for both steps.
- Two CURRENT.md files collide: the newer `opened` stays, the older goes to archive.
- When to write: a deploy succeeded, a config changed, a conclusion was reached, and any moment before the session might be cut off. Do not wait for the session to end.
- A hand-off that comes back from another model is a candidate: `python -X utf8 tools/brain.py handoff review <file>` compares it with this file before it may replace it.

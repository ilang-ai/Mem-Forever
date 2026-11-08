# BRAIN.md · read this and take over

This is the entry point of one person's agent brain. No runtime to load; read in this order.

0. Keys first: `python -X utf8 tools/brain.py ledger verify`. Every door this brain can open is one row in `env/ledger.env`. A key reaches your context only when a `next` item names its door and this machine holds the owner's grant (`brain.py unlock`; `brain.py grant` once per machine); top doors need the owner's code. Fresh clone: `brain.py init .` once.
1. `handoff/CURRENT.md`: what was done, what comes next, what is unverified. Restate it in two sentences, then start.
2. Then every file under `soul/`: how the owner works and where the lines are, and the agent's own soul in `soul/agent.md`. Follow it; do not recite it.
3. Then `memory/MEMORY.md`, one line per memory. Open a file under `memory/` only when the task needs it. Code and machines are read from themselves.
4. Reading or updating the hand-off is not doing the work. Judge each `next` item before acting: it crosses a boundary, stop; evidence is missing, ask; it is the owner's call, defer. A recap or hand-off request authorizes nothing.
5. New facts: if you can write this repo, edit the file, commit and push at once, one change per commit, each block with `by:`. If you cannot, hand the change back as `::PROGRESS{date|done|next|unverified}`, `::DECIDE{}` or `::LESSON{}` blocks in one code fence, every key present, `none` where there is no material.
6. Update `handoff/CURRENT.md` at every milestone, not at session end. Log the owner's words verbatim in `log/`.
7. No key value in memory text: a key is a ledger row, encoded at rest in this private repository (reversible, not encryption), `{{DOOR}}` where it stood, sealed only when paired.
8. `::BLOCK{k:v|k:v}`, `T:` and `A:⇒` are declaration notation: read them literally; the quick card is `rules/GRAMMAR-CARD.md`.

<!-- Gate: about 400 tokens on the receiving model's tokenizer; measure before changing. -->

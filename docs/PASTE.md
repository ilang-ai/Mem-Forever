# Pasting the brain into a chat AI that has no tools

Some chat AIs cannot read a repository: no connector, no sandbox, no files. They can still read this brain and hand changes back, if the message is built right. This is the third way in; the first two are a coding agent with the repo on disk and a chat AI with a connector or a clone.

## Build the message

```
python -X utf8 tools/brain.py paste --out paste.md
```

The message is: one opening line, the notation card, a `---` line, then the declaration blocks of `handoff/CURRENT.md` (frontmatter and the claim-and-close notes left out). Nothing else: no runtime, no spec link. Send it as the first message, as one message. The expected reply is just "done reading".

The card follows the owner's language. `rules/GRAMMAR-CARD.md` is the English card, `rules/GRAMMAR-CARD.zh.md` the Chinese one; `--lang auto` picks by the language of the hand-off, `--lang zh` or `--lang en` overrides, and the opening line follows the card that was picked. Another language is one more file, `rules/GRAMMAR-CARD.<lang>.md`, translated from the English card line by line; it is not measured until you measure it.

The command refuses to build the message when any line looks like a secret; fix the hand-off first.

## One check before real work

Ask: "Restate the hand-off's progress in three parts: done, next, unverified. Item by item, verbatim, keep the numbering." A model that paraphrases, merges items or drops the numbering did not read the notation; use a stronger tier or a shorter hand-off. Do not fix it by adding instructions to the card; the card is measured and tested as it is.

## Taking the answer back

Before you ask for the block, say that items are identifiers: an item moves between `done`, `next` and `unverified` whole, and news goes in a new item. Without that sentence a model rewrites the item it moves, and the review rejects the rewrite as a drop plus an addition.

Whatever comes back is a candidate. Paste it into a file and run

```
python -X utf8 tools/brain.py handoff review returned.md --overlay --out candidate.md
```

against the current hand-off. `--overlay` lays the returned blocks over the baseline by identifier and carries the rest of the baseline in, so one `::PROGRESS{}` block is enough; `--out` writes the composed whole, which is what replaces `handoff/CURRENT.md` when you accept. It rejects a deleted or weakened boundary, a forbidden or unevidenced item in `done`, a missing key, an empty value, a changed identifier and a silent drop; it lists the rest for you to decide. Only an accepted candidate replaces `handoff/CURRENT.md` (see the skill, "Merging a hand-off another model wrote").

## What was measured

- The English card (`rules/GRAMMAR-CARD.md`, 1351 bytes): 381 to 410 tokens on ten models' tokenizers (MiniMax, Grok 4.20 and 4.7, GLM, Kimi, DeepSeek, Qwen, Gemini, GPT, Doubao), 539 on Claude's. Measured 2026-11-04; not yet tested in conversation.
- The Chinese card (`rules/GRAMMAR-CARD.zh.md`, 1212 bytes): 352 to 392 tokens on the same ten, 542 on Claude's. Tested in conversation on twelve model tiers from weak to strong, 2026-11-03 and 2026-11-04.
- `BRAIN.md`, the entry for a chat AI with a connector: 1552 bytes; 399 to 406 tokens on GPT, GLM and Kimi, 427 on Doubao, 588 on Claude's, net of each chat template, measured 2026-11-05 after the 2.1 edit of point 2.
- One web endpoint, 2026-11-05: ChatGPT's web chat, signed out, free tier, no files and no tools. The Chinese card plus a 14-block hand-off went in as one message and came back as "done reading"; the check above restated 4, 6 and 9 items verbatim, confirmed by script. The first write-back rewrote the item it moved and the review rejected it; told the identifier rule, the second write-back passed (one flag, one transition, one addition) and was accepted.

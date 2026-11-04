# Pasting the brain into a chat AI that has no tools

Some chat AIs cannot read a repository: no connector, no sandbox, no files. They can still read this brain and hand changes back, if the message is built right. This is the third way in; the first two are a coding agent with the repo on disk and a chat AI with a connector or a clone.

## Build the message

```
python -X utf8 tools/brain.py paste --out paste.md
```

The message is: one opening line, the notation card `rules/GRAMMAR-CARD.md`, a `---` line, then the declaration blocks of `handoff/CURRENT.md` (frontmatter and the claim-and-close notes left out). Nothing else: no runtime, no spec link. Send it as the first message, as one message. The expected reply is just "done reading".

The command refuses to build the message when any line looks like a secret; fix the hand-off first.

## Five check questions

Ask them before any real work. The answers show whether the model read the notation or guessed.

1. Restate the hand-off's progress in three parts: done, next, unverified. Expected: item by item, verbatim, section numbers kept.
2. Which `next` item conflicts with a boundary, and which fact is tentative? Expected: it names the boundary, offers no way around it, and names the `conf:tentative` fact.
3. Record this decision as a block: a decision you make now, with a reason. Expected: one `::DECIDE{@OWNER}{what:…|why:…|context:…}` inside a code fence, all three keys, attributed to the owner's entity (the `alias` line in the hand-off does this).
4. What time zone do the dates use? Expected: what the hand-off says, or "unknown". An invented zone is a fail.
5. Record this decision: a decision with no reason given. Expected: `why:none`, nothing invented.

A model that fails question 1 or 3 needs a stronger tier or a shorter hand-off. Do not fix it by adding instructions to the card; the card is measured and tested as it is.

## Taking the answer back

Before you ask for the block, say that items are identifiers: an item moves between `done`, `next` and `unverified` whole, and news goes in a new item. Without that sentence a model rewrites the item it moves, and the review rejects the rewrite as a drop plus an addition.

Whatever comes back is a candidate. Paste it into a file and run

```
python -X utf8 tools/brain.py handoff review returned.md --overlay --out candidate.md
```

against the current hand-off. `--overlay` lays the returned blocks over the baseline by identifier and carries the rest of the baseline in, so one `::PROGRESS{}` block is enough; `--out` writes the composed whole, which is what replaces `handoff/CURRENT.md` when you accept. It rejects a deleted or weakened boundary, a forbidden or unevidenced item in `done`, a missing key, an empty value, a changed identifier and a silent drop; it lists the rest for you to decide. Only an accepted candidate replaces `handoff/CURRENT.md` (see the skill, "Merging a hand-off another model wrote").

## What was measured

- The Chinese card: 1212 bytes; 352 to 392 tokens on ten models' tokenizers (MiniMax, Grok 4.20 and 4.7, GLM, Kimi, DeepSeek, Qwen, Gemini, GPT, Doubao), 542 on Claude's. Tested with the five questions on twelve model tiers from weak to strong, 2026-11-03 and 2026-11-04.
- The English card (`brain.py init` writes it): 1351 bytes; 381 to 410 tokens on the same ten, 539 on Claude's. Measured, not yet question-tested.
- `BRAIN.md`, the entry for a chat AI with a connector: 1552 bytes; 399 to 406 tokens on GPT, GLM and Kimi, 427 on Doubao, 588 on Claude's, net of each chat template, measured 2026-11-05 after the 2.1 edit of point 2.
- One web endpoint, 2026-11-05: ChatGPT's web chat, signed out, free tier, no files and no tools. The Chinese card plus a 14-block hand-off went in as one message and came back as "done reading"; question 1 restated 4, 6 and 9 items verbatim, checked by script. The first write-back rewrote the item it moved and the review rejected it; told the identifier rule, the second write-back passed (one flag, one transition, one addition) and was accepted.
- Three rules on the card came out of those runs. The fence sentence is the first clause of the write-back rule, because weak tiers dropped the fence when it came later. `when:` is described as a condition and not a release clause, because boundaries were argued around otherwise. The owner entity carries `alias:the I in this chat`, because decisions were attributed to invented entities otherwise.

# PRODUCT record · Mem-Forever landing page

Record for the public page of this repository, kept with the page. Facts come from the repository and its releases; anything not on record is marked inferred.

## Platform

Web. One static page served by GitHub Pages from this `docs/` folder, plus the repository README, which is the engineering book.

## Stack

Static HTML and CSS in a single file (`docs/index.html`), no build step, no script required for content. System font stacks only; no web font requests.

## Users

People who run AI agents and want the agent to remember them across sessions, tools and machines: developers using Claude Code, Cursor, Codex, Copilot or Gemini CLI, and people who work in web chats with no tools. English and Chinese readers (the README exists in both; the notation card ships in both languages). Inferred: most arrive from GitHub, X or a search, already knowing what an agent is.

## Product purpose

Keep a person's memory in their own private Git repository as small Markdown files an agent can read and write: a profile, one file per memory, a hand-off note that says what was done, what comes next and what is unverified, and a ledger of every door it can open, a key reaching it only when the work reaches that door. Let the next session, in any tool, pick up where the last one stopped.

## Positioning

A Git-native memory layer on the iLang protocol. Unlike hosted memory services, there is no server, no account and no telemetry; the user owns the files. Unlike plugin-per-tool approaches, any tool that reads files can use it, and a chat with no tools gets it pasted.

## Operating context

GitHub Pages at `https://ilang-ai.github.io/Mem-Forever/`, the repository at `https://github.com/ilang-ai/Mem-Forever`, the organisation site at `https://ilang.ai`. Read on desktop and phone, in light or dark system schemes.

## Capabilities and constraints

The page may link to the repository, the README in English and Chinese, the release, the DOI and ilang.ai. It must not claim numbers that were not measured, invent testimonials, customers or awards, or show secrets. Example data on the page is labelled as example data.

## Brand commitments

Inherit the iLang world: paper and ink schemes (`#e9eaec` / `#121314` and `#1a1b1d` / `#ececec`), the gold signal (`#e0b96a` on ink, `#9a6f22` / `#7a5a1c` on paper), hairline rules at the brand's two alphas, pill controls, the system sans stack led by Bahnschrift / SF Pro / Segoe UI / Noto Sans, the mono stack for notation, the bracket mark. Mem-Forever adds one object of its own: the hand-off note on a ruler of sessions.

## Evidence on hand

Release v2.1.0 (2026-11-05), Zenodo concept DOI 10.5281/zenodo.22865160 (version DOI 10.5281/zenodo.23958957). Token measurements on real tokenizers: English card 381 to 410 on ten models and 539 on Claude; Chinese card 352 to 392 and 542; BRAIN.md 399 to 406 on GPT, GLM and Kimi, 427 on Doubao, 588 on Claude. A signed-out web chat read the card and a 14-block hand-off in one message and restated 4, 6 and 9 items verbatim; its write-back was reviewed, corrected once and accepted (2026-11-05). Every template file with notation passes the iLang grammar validator with zero errors and zero warnings. The review output shown on the page is a real run of `brain.py handoff review` (2026-11-05) on an example hand-off whose candidate dropped the boundary, emptied a decision's reason and dropped a next item: 3 REJECT, 1 FLAG, 1 TRANSITION, exit 1. The word REJECT appears three times on the page because the run printed it three times; it is evidence, not decoration, and the repeated-text rule is waived for that block on that ground.

## Product principles

1. Say only what was measured or observed; label example data.
2. The page reads in the order a new visitor needs: what it is, how to get in, what a session does, how a hand-off is protected, the numbers.
3. One primary action: create the repository from the template. One secondary: read the book.
4. The page is a child of the iLang world, not a new brand.
5. It works without script, in both schemes, on a phone.

## Accessibility and inclusion

Semantic headings in order, a skip link, visible focus rings, contrast at or above 4.5:1 for body text in both schemes, body lines at most 76 characters (a 62ch column, measured at 1440), text sizes at or above 14px, reduced-motion alternative for the one motion moment, Chinese link marked with its language.

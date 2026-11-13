# Changelog

One `## YYYY-MM-DD` section per day, newest first, prose bullets (OKF v0.2 reserved file). Record changes to the layout, rules and tools here. Memories go to `memory/`, progress goes to `handoff/CURRENT.md`.

## 2026-11-13

- `hermes/`: the brain as a Hermes Agent memory provider plugin (`hermes plugins install mem-forever`, `hermes memory setup`). At session start it saves what a previous session left under `soul/ memory/ handoff/ log/`, pulls the brain and puts `BRAIN.md` in the system prompt; the first turn gets the hand-off, the soul and the index; the owner's words go to `log/` through `brain.py log owner`; before compression and at session end it commits and pushes the four directories and hands the `::PROGRESS` line to the summary; one tool `mem_forever` runs the engine (status, check, ledger_verify, unlock, handoff_review, recognize, log, commit, pull). Subagent and cron runs read only. `hermes/skills/mem-forever/SKILL.md` is the same skill body; `hermes/test_hermes_plugin.py` runs 33 scenarios in a temporary brain with or without Hermes installed. Version stays 3.2.0.

## 2026-11-08

- Mem-Forever 3.1: a value has three states (plain in a process, encoded at rest with `env/pepper`, sealed when pairing); grants live in the machine's git config (`brain.py grant`); the secret scan harvests into ledger rows instead of refusing commits (`ledger harvest`, `migrate-cc`); `evidence add` records `owner_claimed` unless a transcript backs it; `unlock` takes the hand-off scope; `check` warns when the hooks are off on a clone; `paste` masks. brain.py 2.1, 37 scenarios.
- Mem-Forever 3.0: the ledger (`env/ledger.env`) replaces the vault; `log/` keeps the owner's words; `brain.py` 2.0 adds ledger, unlock, otp, pair, unseal, log, recognize, evidence, provenance, review, import, verify, instructions, remote-check, migrate-2to3; hooks under `tools/hooks/`; every block carries `by:`.
- Repository created from the Mem-Forever template.

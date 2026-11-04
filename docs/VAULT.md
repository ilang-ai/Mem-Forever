# VAULT: keys travel with the brain, encrypted

The brain repo holds everything an agent needs to continue your work on a new machine, including credentials, but no credential ever sits in the repo as plain text. `vault/` holds one [age](https://age-encryption.org) encrypted bundle; `vault/recipients.txt` holds the public key; the private key lives in your password manager and on a printed sheet. The private key is the only thing in this design that never enters any cloud.

## Tooling

[age](https://github.com/FiloSottile/age) is a single binary, no gpg. Install it with your package manager (`winget install --id FiloSottile.age -e`, `brew install age`, `apt install age`). `tools/brain.py` finds it on `PATH`, in the winget package folder, or where `--age-dir` or the `BRAIN_AGE_DIR` variable points.

## One-time setup

```
age-keygen -o ~/.age/key.txt
age-keygen -y ~/.age/key.txt > vault/recipients.txt
```

Store the content of `~/.age/key.txt` in a password manager secure note and print one copy. Never `cat` it into a chat, a commit message, a hand-off or a log; an agent that runs these commands must not read or repeat it either. Commit `vault/recipients.txt`; it is public.

## What goes into the bundle

`python -X utf8 tools/brain.py vault pack` builds a tar in memory and encrypts it to `vault/keys-YYYY-MM-DD.age`:

| Member | Source | How |
|---|---|---|
| `keys/<name>.env` | every `*.env` in your keys directory (default `~/.keys`) | byte for byte; the tool never parses or prints them |
| `ssh/<name>` | private keys in `~/.ssh` (files named `id_*` without `.pub`) | byte for byte |
| `memory-values.json` | the values behind every `[REDACTED <kind> <fingerprint>]` marker in `memory/` | looked up in the unredacted source memory, checked against the fingerprint |
| `MANIFEST.json` | size and sha256 of each member, time, host | for `verify` |

No plain-text intermediate file is written. The tool prints file names, byte counts, kinds and fingerprints, never values. Commit the `.age` file; `check` skips binary files.

## Redaction markers and fingerprints

Memory text never carries a credential value. It carries a marker, written `[REDACTED <kind> <fingerprint>]`.

`kind` is a lower-case slug that says which key it is and whose (for example `db-password-staging`, `cloud-account-id-main`). `fingerprint` is derived from the value: strip a well-known vendor prefix if there is one (the OpenAI-style, GitHub token, and similar prefixes the tool knows), then take the first 4 and last 4 characters when the remainder is 24 characters or longer, otherwise the first 2 and last 2, joined by `...`. Short values show fewer characters on purpose, so a ten-character password does not leak most of itself through its fingerprint.

The same value in several places gets the same marker, and the bundle stores it once. A marker whose value cannot be found in the source (because the source itself only ever held a fingerprint) is listed as `unresolved` in the bundle and in the tool's output; the tool never guesses.

Configuration files under `env/` use `${VAULT:<name>}` placeholders instead of markers; `install` fills them from the unlocked bundle.

## Verify, unpack, new machine

```
python -X utf8 tools/brain.py vault verify          # decrypts in memory, compares every member's sha256 with the original, checks markers against values
python -X utf8 tools/brain.py vault unpack --to DIR # extracts to a directory, for a round-trip test; delete DIR afterwards
python -X utf8 tools/brain.py vault unpack          # restores keys/ to ~/.keys and ssh/ to ~/.ssh; existing files are not overwritten
```

On a new machine the order is: install git, python, age and your agent CLI; put the private key at `~/.age/key.txt` from the password manager (the only step that needs a human); clone the brain; `vault unpack`; `brain.py install`. The whole thing should take under thirty minutes; if it does not, the bottleneck is a finding to record in `log.md`.

## Rotation and leaks

- A value that reached git history before it was redacted: with no remote yet, reset the history and run `git gc --prune=now`; with a remote, treat it as leaked, rotate the value first, then clean the history.
- Rotated a value: edit the source memory, repack, commit the new `.age`. Old bundles in history are still only readable with the private key.
- Lost the private key: every bundle is unreadable. That is why it is in the password manager and on paper.

## Boundaries

- The agent never reads the key files or the private key; it only runs the tool, which handles bytes.
- `check` must report zero secret-like hits before every push. It scans for vendor token prefixes, private key blocks, JWTs, bearer headers, passwords inside URLs, `password:`-style lines and hex strings next to words like secret or token. If it flags a false positive, redact anyway or move the text out of the repo; do not weaken the scanner for one file.

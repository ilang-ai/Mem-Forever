# LEDGER: keys are where the brain starts

Memory in this template is a derivation: the keys derive the tasks, the tasks yield constants, and the logic between them is written as annotations. The ledger is the start of that derivation. `env/ledger.env` holds one row per door the brain can open: a machine, an API, a repository, an account. Nothing in a memory file ever carries a key value; the ledger does.

The threat model is the owner's, stated 2026-11-08: for one person, losing a key costs more than leaking one. Keys are replaceable; being locked out of your own machines is not. So a value has three states and none of them needs anything outside this **private** repository: plain only inside a process, encoded at rest (3.1), sealed only when pairing. The push guard keeps the repository private; the owner is always a recipient of anything sealed, and `ledger decode` opens everything for the owner with nothing but the repository.

## One row per door

```
::STATE{@HK, door:ssh root@203.0.113.5, kind:ssh_password, ref:HK, verify:ssh -o BatchMode=yes root@203.0.113.5 true, last_verified:2026-11-08, recover:provider console; second key in env/ssh/hk, scope:fleet, top:false, why:hub_of_the_fleet}
```

| Field | Meaning |
|---|---|
| `@NAME` | the row's name, upper case like every canon entity (`ledger add hk` writes `@HK`); a `next` item names the door by this name, any case |
| `door` | what the key opens |
| `kind` | `ssh_password`, `ssh_key`, `api_key`, `token`, `env_file`, `value`, or a top kind (below) |
| `value` or `ref` | the value inline, or `ref:KEY` pointing at a `KEY=enc1:...` line in `env/keys.env` (encoded at rest since 3.1; plain rows are still read and `ledger encode` converts them) |
| `grant` | `once` or `standing` (3.1); default `once` for a top kind, `standing` for the rest; see Grants |
| `verify` | a command whose exit 0 means the door opens; `$LEDGER_VALUE` and `$<REF>` are set when it runs |
| `last_verified` | the date `verify` last passed; `none` until then |
| `recover` | how to get back in when the key is lost: console, rescue mode, a second key, who else holds one |
| `scope` | tags that decide which rows a pairing may carry |
| `top` | `true` for a door that never unlocks from the record |
| `why` | what the door serves: the function or constant it exists for |

Top kinds are `root`, `sudo`, `payment`, `account_security`, `recovery_code`, `registrar`, `dns`, `age_identity`. A row of a top kind is a top door whatever `top:` says.

```
python -X utf8 tools/brain.py ledger add hk --door "ssh root@203.0.113.5" --kind ssh_password --value '<value>' --verify 'ssh -o BatchMode=yes root@203.0.113.5 true' --recover 'provider console' --scope fleet --why hub
python -X utf8 tools/brain.py ledger list          # masked, with the stale rows named
python -X utf8 tools/brain.py ledger verify all    # runs every verify, writes last_verified, exit 1 when a door is shut
python -X utf8 tools/brain.py ledger show hk --with-value
```

`verify` is what gives decay a physical meaning: a row unverified for 90 days is stale and is listed at the next session start; nothing is deleted on its own.

## Three states (3.1)

A key value is **plain** only inside a process: in the tool during `unlock`, in the agent's context after it, in the owner's terminal when he asks. At rest in `env/keys.env` it is **encoded**: `KEY=enc1:<base64url>`, the bytes xored with a keystream `SHA-256(pepper || door || counter)`, the pepper being 32 random bytes in `env/pepper`, written once by `init` and committed with the repository. This is obfuscation against accidental exposure (grep, screenshots, model context, logs, pastes); it is **not encryption**: anyone holding the repository and this tool reads every value, which is exactly the owner's threat model. **Sealed** is the third state, for a receiver outside the repository: age to the receiver's key and always to the owner's (Pairing, below).

```
python -X utf8 tools/brain.py ledger encode              # 3.0 plain rows -> enc1; keeps env/keys.env.bak until you have seen decode open them
python -X utf8 tools/brain.py ledger decode              # every row plain, for the owner's terminal; needs nothing but the repository
python -X utf8 tools/brain.py ledger decode --pepper <hex>   # if env/pepper was lost and you kept its hex elsewhere (optional)
python -X utf8 tools/brain.py ledger reveal HK            # one door's plain value
```

A lost pepper is a lost repository, nothing less and nothing more; the pepper is a file of the repository, so a clone is complete. The word *encryption* is used in these documents only for the sealed state.

## Grants: a door opens on this machine after the owner's nod (3.1)

A grant is a line of **this machine's** git config, never a file of the repository: `brain.grant.<DOOR> true` for one door, `brain.grant.all true` for every standing door, `brain.grant.write true` for storing new keys. The owner says yes once; the tool records it:

```
python -X utf8 tools/brain.py grant HK          # this door, this machine
python -X utf8 tools/brain.py grant --all       # every standing door on this machine (never a top or once door)
python -X utf8 tools/brain.py grant --write     # storing new keys here: ledger add --value, ledger harvest, migrate-cc
python -X utf8 tools/brain.py grant --list      # what this machine holds
python -X utf8 tools/brain.py grant --revoke HK # take one back (--revoke --all)
```

Every row is `grant:once` or `grant:standing`. Top kinds are `once` and keep the one-time code of 3.0; every other kind is `standing` unless the row says otherwise. `unlock` of a standing door is refused, with the exact `grant` command, until this machine holds the grant; a new machine therefore costs one nod at the first unlock, and that is the whole ceremony. A copied or stolen repository carries no grant, so the tool refuses to unlock for the agent; the holder can decode by hand, which the threat model accepts. The grant disciplines the agent, not a thief.

## A key arrives with the task

`brain.py unlock <name>` prints a row with its value, the moment the key enters the model's context. It refuses unless a `next` item in `handoff/CURRENT.md` names the door, unless this machine holds the grant, and unless the row's scope lies inside the declared scope: `--scope`, or since 3.1 the `scope:` key of the `::PROGRESS{}` block; a row that has a scope and finds none declared is refused and says so. A top door is refused always; the owner, in person, runs `brain.py otp issue <name>` and hands the code over; `brain.py unlock <name> --code <code>` uses it once, and it expires on its own. Every unlock is written to `log/`.

Nothing is handed over at the start. A new machine, a new agent or a bulk import gets a key only when the work reaches its door.

## Pairing: seal only when leaving the repository

A receiver that holds the repository reads every row directly; for it, `unlock` is context discipline. Sealing is for a receiver without repository access: another person's scope, or a model that gets rows by paste.

```
python -X utf8 tools/brain.py pair <age1-public-key-or-file> --scope fleet,writing
python -X utf8 tools/brain.py unseal pair/2026-11-08-<label>/HK.age        # the owner's key opens it
```

`pair` seals the rows inside the declared scope, one file per row, to the receiver's key **and** to every key in `vault/recipients.txt`, and writes `declaration.md`: identity, scope, authorization source, the rows carried. Top doors are never sealed. The owner's private key stays in a password manager and on paper, as in 2.1; it is the owner-recipient key now, not a lock on the brain.

## Harvest: the scan collects instead of refusing (3.1)

A key-shaped string under `memory/`, `soul/` or `handoff/` is no longer a refused commit. `brain.py check` reports it as one WARN with the command; `brain.py ledger harvest` turns each one into a door: a row named `<KIND>_<SOURCE_STEM>` with `verify:none`, the value encoded into `env/keys.env`, and the text replaced by `{{DOOR}}`. `ledger reveal <DOOR>` shows the value, so the replacement is reversible. `log/` and `soul/evidence.md` are never touched. `migrate-cc` runs the harvest over what it copied, so a memory migrated from Claude Code arrives with its doors in the ledger instead of 136 refused commits. `verify:none` makes `ledger verify` list the door as never verified; the first session asks the owner once for the command or marks the door dead.

## The pasted brain carries no values

`brain.py paste` adds the ledger to the message a chat AI with no tools receives: each row with its door, kind, verify, recover and last verified date, and **no value**. Since 3.1 any key-shaped string left in the message is masked to `{{UNHARVESTED <kind> <fingerprint>}}` instead of refusing the paste; `env/pepper`, `env/keys.env`, `log/` and `pair/` are never in it. That model cannot open a door, and the message leaves the private repository. `--with-values` puts the values back for the owner who means to hand everything to a model that has a shell.

## Private means private

`brain.py check` does not scan `env/`, `log/` or `pair/` for secret-like text; it scans `soul/`, `memory/`, `handoff/` and the docs and, since 3.1, reports what it finds as a WARN with the harvest command, never as a refused commit. `tools/hooks/pre-push`, installed by `brain.py install` and `brain.py init`, refuses a push that carries memory to a remote that is public: GitHub and Gitee are asked through their API (`brain.py remote-check <url>`); a remote the check cannot read needs a one-time confirmation, `git config --bool brain.allowPush.<remote> true`.

## Coming from the 2.1 vault

```
python -X utf8 tools/brain.py migrate-2to3            # owner runs it; needs ~/.age/key.txt
```

It opens the latest `vault/keys-*.age`, writes `keys/*.env` under `env/`, SSH keys under `env/ssh/`, the redacted memory values into `env/keys.env` encoded (3.1), one ledger row for each, then stamps every block `by:legacy` (`provenance init`). Fill `verify` and `recover` for each row, run `ledger verify all`, commit. The old `.age` files stay in git history. `vault pack`, `vault unpack` and `vault verify` remain for reading old bundles.

## The one thing that must always work

Download everything and hand it to any model: the card, the hand-off, the ledger. With `--with-values` it is the whole brain. No step of unlocking depends on a model reasoning; `brain.py` is the one that opens things, and the owner can run it alone: `ledger decode` needs the repository and nothing else, no grant, no passphrase, no second device.

Recognition anchors (`words:` on the `T:` and `A:` lines of `soul/soul.md`) hold the owner's own words, the ones an agent never writes, not topic words; topic words recognize whoever talks about the same work.

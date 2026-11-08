# LEDGER: keys are where the brain starts

Memory in this template is a derivation: the keys derive the tasks, the tasks yield constants, and the logic between them is written as annotations. The ledger is the start of that derivation. `env/ledger.env` holds one row per door the brain can open: a machine, an API, a repository, an account. Nothing in a memory file ever carries a key value; the ledger does.

The threat model is the owner's, stated 2026-11-08: for one person, losing a key costs more than leaking one. Keys are replaceable; being locked out of your own machines is not. So the rows sit plain in this **private** repository, and encryption is a pairing act, not a storage state. The push guard keeps the repository private; the owner is always a recipient of anything sealed.

## One row per door

```
::STATE{@HK, door:ssh root@203.0.113.5, kind:ssh_password, ref:HK, verify:ssh -o BatchMode=yes root@203.0.113.5 true, last_verified:2026-11-08, recover:provider console; second key in env/ssh/hk, scope:fleet, top:false, why:hub_of_the_fleet}
```

| Field | Meaning |
|---|---|
| `@NAME` | the row's name, upper case like every canon entity (`ledger add hk` writes `@HK`); a `next` item names the door by this name, any case |
| `door` | what the key opens |
| `kind` | `ssh_password`, `ssh_key`, `api_key`, `token`, `env_file`, `value`, or a top kind (below) |
| `value` or `ref` | the value inline, or `ref:KEY` pointing at a `KEY=value` line in `env/keys.env` |
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

## A key arrives with the task

`brain.py unlock <name>` prints a row with its value, the moment the key enters the model's context. It refuses unless a `next` item in `handoff/CURRENT.md` names the door, and unless the row's scope lies inside the scope the receiver declared (`--scope`). A top door is refused always; the owner, in person, runs `brain.py otp issue <name>` and hands the code over; `brain.py unlock <name> --code <code>` uses it once, and it expires on its own. Every unlock is written to `log/`.

Nothing is handed over at the start. A new machine, a new agent or a bulk import gets a key only when the work reaches its door.

## Pairing: seal only when leaving the repository

A receiver that holds the repository reads every row directly; for it, `unlock` is context discipline. Sealing is for a receiver without repository access: another person's scope, or a model that gets rows by paste.

```
python -X utf8 tools/brain.py pair <age1-public-key-or-file> --scope fleet,writing
python -X utf8 tools/brain.py unseal pair/2026-11-08-<label>/HK.age        # the owner's key opens it
```

`pair` seals the rows inside the declared scope, one file per row, to the receiver's key **and** to every key in `vault/recipients.txt`, and writes `declaration.md`: identity, scope, authorization source, the rows carried. Top doors are never sealed. The owner's private key stays in a password manager and on paper, as in 2.1; it is the owner-recipient key now, not a lock on the brain.

## The pasted brain carries no values

`brain.py paste` adds the ledger to the message a chat AI with no tools receives: each row with its door, kind, verify, recover and last verified date, and **no value**. That model cannot open a door, and the message leaves the private repository. `--with-values` puts the values back for the owner who means to hand everything to a model that has a shell.

## Private means private

`brain.py check` no longer scans `env/`, `log/` or `pair/` for secret-like text; it still scans `soul/`, `memory/`, `handoff/` and the docs. `tools/hooks/pre-push`, installed by `brain.py install` and `brain.py init`, refuses a push that carries memory to a remote that is public: GitHub and Gitee are asked through their API (`brain.py remote-check <url>`); a remote the check cannot read needs a one-time confirmation, `git config --bool brain.allowPush.<remote> true`.

## Coming from the 2.1 vault

```
python -X utf8 tools/brain.py migrate-2to3            # owner runs it; needs ~/.age/key.txt
```

It opens the latest `vault/keys-*.age`, writes `keys/*.env` under `env/`, SSH keys under `env/ssh/`, the redacted memory values into `env/keys.env`, one ledger row for each, then stamps every block `by:legacy` (`provenance init`). Fill `verify` and `recover` for each row, run `ledger verify all`, commit. The old `.age` files stay in git history. `vault pack`, `vault unpack` and `vault verify` remain for reading old bundles.

## The one thing that must always work

Download everything and hand it to any model: the card, the hand-off, the ledger. With `--with-values` it is the whole brain. No step of unlocking depends on a model reasoning; `brain.py` is the one that opens things, and the owner can run it alone.

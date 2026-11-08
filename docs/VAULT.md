# VAULT: retired in 3.0, see LEDGER.md

The 2.1 vault, one age-encrypted bundle of every key, is retired. Keys now live as rows in `env/ledger.env`, plain in the private repository, and sealing happens only when the brain is paired with a receiver that does not hold the repository. Read [docs/LEDGER.md](LEDGER.md).

What survives from this page:

- the owner's age private key, kept in a password manager and on paper; it is now the owner-recipient key of every `brain.py pair`, so anything sealed always opens for the owner;
- `vault/recipients.txt`, the owner's public key(s), committed;
- `brain.py vault pack / unpack / verify`, kept for reading bundles made by 2.1; `brain.py migrate-2to3` turns such a bundle into ledger rows.

Redaction markers `[REDACTED <kind> <fingerprint>]` in memory text are still honoured by `migrate-2to3` and by the vault commands; new memories name the door instead of carrying a marker.

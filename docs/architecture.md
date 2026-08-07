# Architecture

## Why this exists

NeverSink/FilterBlade's PoE2 filter is already free and already economy-tuned — the only thing
behind their Patreon is auto-delivery: pushing the freshest filter into your game folder so you
don't have to manually re-download it. This project builds a free equivalent, using its own
tiering logic derived from live poe.ninja data (not their curated filter content), so it doesn't
undercut the project their Patreon funds.

## Data source

poe.ninja exposes PoE2 economy data as plain JSON, no HTML scraping needed:

- `GET /poe2/api/economy/leagues` — used to resolve the active challenge league dynamically, so
  it's never hardcoded and stays correct across league launches.
- `GET /poe2/api/economy/exchange/current/overview?league={league}&type=Currency` — currency
  prices. Response has `core.rates` (conversion rates to Exalted/Chaos), a **top-level** `items[]`
  array (id → display name lookup — note this is *not* the same as `core.items[]`, which only
  holds the 2-3 reference currencies used for rate conversion), and `lines[]` (the actual prices,
  keyed by `id` only).
- `GET /poe2/api/economy/stash/current/item/overview?league={league}&type={type}` — unique item
  prices, one call per unique subtype (weapons, armours, accessories, flasks, charms, jewels,
  sanctum relics). `lines[]` here already includes `name` and `baseType` directly.
- No PoE2 Waystones endpoint exists (confirmed via a live 404) — out of scope until poe.ninja adds
  one.
- A full daily run makes on the order of ten requests total, well inside poe.ninja's "don't poll
  faster than a few minutes" guidance.

## Tiering

`.filter` files match static conditions, not live price expressions, so "tiering" means: normalize
each item's price to an exalted-equivalent baseline, filter out low-confidence lines, bucket into
ordered tiers by cutoff, and emit one `Show`/`Hide` block per tier listing every matching
`BaseType`.

Currency and uniques are handled differently because they mean different things:

- **Currency** always drops fully identified, so each currency's own name maps 1:1 to a filter
  condition.
- **Uniques** drop unidentified, and a filter can only ever match `BaseType` (e.g. "Shortsword"),
  never a unique's own name (e.g. "Redbeak") — confirmed against GGG's own forums, where this was
  requested as a feature and never implemented. So uniques are grouped by shared base type and
  priced at the *highest* value among all uniques that can roll on that base — a base type is
  never under-valued just because one of its uniques is junk.
- Confidence for a grouped base type comes from the `listingCount` of whichever specific line set
  the max price, not a sum across the group — otherwise a thinly-traded outlier on one unique
  could "borrow" confidence from unrelated items sharing the same base type. This was found via a
  real bug during development: a 9-listing outlier price on "Redbeak" was inflating the entire
  "Shortsword" base type until confidence was scoped to the specific price being trusted.
- Unique `Show`/`Hide` blocks always include `Rarity == Unique` so they don't also catch normal/
  magic/rare items of the same base type.
- The generator never emits a blanket `Hide` — only categories it has actually priced get rules;
  everything else falls through to the game's default visibility.

## Pipeline

```
generator/poe_ninja_client.py   -> raw JSON from poe.ninja
generator/league.py             -> resolves the active league
generator/tiering.py            -> raw JSON -> PricedItem[] -> Tier[]
generator/filter_builder.py     -> Tier[] -> .filter text + manifest.json
generator/validate.py           -> sanity checks before anything gets committed
generator/main.py               -> CLI orchestrator (used by GitHub Actions and locally)
```

`.github/workflows/generate-filter.yml` runs this daily, validates the output, and commits
`dist/community-loot-filter.filter` + `dist/manifest.json` only if something actually changed. If
any category's fetch fails or comes back empty, the job aborts without committing — a broken or
partial filter is never published.

## Client delivery

`client_updater/` is a separate, independently-shipped Python package (kept dependency-light —
just `requests` — to keep the compiled `.exe` small):

```
client_updater/paths.py      -> locates the PoE2 filter folder and local state/log files
client_updater/updater.py    -> fetch manifest -> compare hash -> download -> atomic replace
client_updater/scheduler.py  -> registers/removes a Windows Task Scheduler entry
client_updater/cli.py        -> install / run / uninstall
```

- Installs to a distinctly-named `CommunityAutoFilter.filter` rather than overwriting any
  existing filter, so it shows up as its own option in PoE2's filter dropdown.
- Downloads to a temp file and uses `os.replace()` (atomic on the same volume) to swap it in, so
  a failed/partial download never corrupts the live file.
- Scheduling uses a plain recurring `/SC HOURLY /MO <n>` trigger. `/SC ONLOGON` was tried first
  and rejected outright by `schtasks` (`/RI`/`/DU` aren't valid with logon-type triggers — this
  was verified against the real Windows Task Scheduler, not assumed). Deliberately omits `/RU`/
  `/RP` (run-as-user credentials), so the task defaults to "only run while the installing user is
  logged in" — no Windows password ever needs to be stored.
- Packaged via PyInstaller (`client_updater/updater.spec`) into a single `.exe`, built by
  `.github/workflows/build-client.yml` and attached to GitHub Releases.

## Deferred (not MVP)

- Waystones (no poe.ninja PoE2 endpoint exists yet).
- Static/non-price rules for rares, normals, and magic items (item level, sockets, rarity-based
  clutter hiding).
- Any category beyond Currency + Uniques (fragments, essences, runes, etc. — same mechanism, just
  more `config/tiers_*.yaml` files and endpoint types).
- Code-signing the client `.exe`.

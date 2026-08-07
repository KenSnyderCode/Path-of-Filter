# Community PoE2 Loot Filter

A free, automatically-updating [Path of Exile 2](https://www.pathofexile.com/) item filter. It's
regenerated daily from live [poe.ninja](https://poe.ninja/poe2) market data, and a small background
tool keeps it current on your machine — no manual re-downloading, no subscription.

**This is an independent, community-run project.** It isn't affiliated with GGG, poe.ninja,
NeverSink, or FilterBlade. Their [NeverSink filter](https://github.com/NeverSinkDev/NeverSink-Filter-for-PoE2)
is also free and already economy-tuned — the only thing behind their Patreon is the auto-delivery
mechanic, which is exactly the gap this project fills, using entirely original tiering logic
derived from live market data rather than their curated filter content.

## For players

1. Download `PoE2LootFilterUpdater.exe` from the [Releases page](../../releases) (link becomes
   live once the project's first client build is published).
2. Run it once: `PoE2LootFilterUpdater.exe install`
   - Windows SmartScreen will likely warn that this is an unrecognized app, since it's an
     unsigned open-source binary — click **More info → Run anyway**.
   - This installs the current filter to your PoE2 folder as `CommunityAutoFilter.filter` and
     registers a background task that rechecks for updates every few hours.
3. In-game: **Escape → Options → Game → Filters**, select `CommunityAutoFilter`.

To stop the background updates later, run `PoE2LootFilterUpdater.exe uninstall`. This only removes
the scheduled task — your currently installed filter file is left in place.

### What this filter currently covers

Currency and Unique items only — the two categories genuinely driven by live prices. Everything
else (weapons, armour, gems, waystones, etc.) intentionally falls through to the game's own
default visibility; this filter never hides a category it hasn't priced.

Unique items drop unidentified in PoE2, so a filter can only ever match a unique's **base type**
(e.g. "Shortsword"), never its specific name (e.g. "Redbeak") — confirmed against GGG's own
forums. This filter therefore tiers unique base types by the highest value among every unique that
can roll on them, so a base type is never under-valued just because one of its uniques happens to
be junk.

## How it works

- `generator/` runs daily via GitHub Actions: fetches PoE2 economy data directly from poe.ninja's
  JSON API, buckets currencies and unique base types into price tiers, and writes
  `dist/community-loot-filter.filter` + `dist/manifest.json`.
- `client_updater/` is the small tool players install: it checks `manifest.json`, and only
  downloads the full filter when its hash has actually changed, then atomically replaces the
  local file.

See [`docs/architecture.md`](docs/architecture.md) for the full design.

## Development

```powershell
python -m venv .venv
.venv\Scripts\pip install -r generator\requirements-dev.txt -r client_updater\requirements.txt

# Run the generator against live poe.ninja data
.venv\Scripts\python -m generator.main

# Run the test suite (uses recorded fixtures, no live network calls)
.venv\Scripts\python -m pytest -q

# Build the player-facing updater exe
.venv\Scripts\pip install pyinstaller
cd client_updater
..\.venv\Scripts\pyinstaller --distpath pyinstaller_dist --workpath pyinstaller_build updater.spec
```

Before the first real release, replace the placeholder `REPLACE_ME/REPLACE_ME` GitHub org/repo in
`client_updater/cli.py`'s `DEFAULT_MANIFEST_URL` / `DEFAULT_FILTER_URL` with the real repo path.

## License

[MIT](LICENSE).

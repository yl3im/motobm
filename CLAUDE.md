# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git workflow

- **Never `git commit` or `git push` without the user's explicit consent.** Do the work,
  then stop and ask.
- When asking, show the list of changed files (e.g. `git status` / `git diff --stat`)
  alongside the question so the user can see exactly what would be committed.
- Only commit and push after the user explicitly says yes. A "yes" approves that one
  set of changes — ask again for the next commit.

## What this is

A single-file Python CLI (`zone.py`) that downloads the BrandMeister DMR repeater
list and emits Motorola MOTOTRBO **CPS2** zone files (XML) for import into Motorola
DMR radios. Repeaters are filtered by band and by country (MCC), QTH locator, or GPS
coordinates. There is no package structure, no test suite, and no build step — it is
run directly as a script.

## Commands

```bash
# Set up environment (a .venv already exists in the repo)
pip install -r requirements.txt

# Run (always requires -n, -b, and -t)
./zone.py -n 'Germany'  -b vhf -t mcc -m 262 -6 -zc 16
./zone.py -n 'Paris'    -b uhf -t qth -q JN18EU -r 150 -6
./zone.py -n 'Stockholm' -b uhf -t gps -lat 59.225 -lon 18.250 -6

# Force re-download of the repeater list
./zone.py ... -f
```

Negative GPS coordinates must be quoted with a leading space or written as
`-lon=-93.2780`, otherwise argparse treats them as flags.

## Architecture

The whole pipeline lives in `zone.py` and runs top-to-bottom in `__main__`:

1. `download_file()` — fetches `bm_url` (BrandMeister `/v2/device`) into `BM.json`,
   only if the file is missing or `-f`/`--force` is given. TLS verification is
   intentionally disabled (`verify=False`) because of the upstream cert.
2. `filter_list()` — reads `BM.json`, sorts by callsign + id, and applies all filters,
   building `filtered_list`. Deduplicates by (rx, tx, callsign). The module-level
   `existing` dict counts how many repeaters share a callsign so duplicates get
   `#N` suffixes later.
3. Output, one of two modes:
   - **Default:** `process_channels()` chunks `filtered_list` into zones of
     `--zone-capacity` channels, calls `format_channel()` per repeater, writes one
     `<zone alias>.xml` per chunk, and prints a `tabulate` summary table.
   - **`-js`/`--javascript`:** `create_js()` prints repeater objects for an external
     web map instead of writing XML.

### Channel generation detail

`format_channel()` emits raw CPS2 XML by string interpolation (no XML library).
A repeater with `rx == tx` (simplex/hotspot) produces a single SLOT2 personality;
otherwise it produces paired **TS1** and **TS2** personalities. Contents of
`custom-values.xml` are spliced into every channel only when `-c`/`--customize` is set.

### JS mode is a different beast

`-js`/`--javascript` is a private feature on the `js` branch for the maintainer's own
internal use — it is not part of the upstream tool and should not be merged to `main`
or treated as a general feature. It changes filtering semantics, not just output: in
`filter_list()` the band and location/MCC filters are **skipped entirely** when
`args.javascript` is set (only `-p`, `-6`, `-cs` still apply). `create_js()`
additionally drops repeaters with no coordinates and any id starting with `247`.

## Conventions and gotchas

- State flows through module-level globals (`filtered_list`, `existing`,
  `custom_values`, `qth_coords`) mutated via `global` — not return values.
- `-m`/`--mcc` accepts a numeric MCC prefix *or* a two-letter country code, which is
  resolved to MCC(s) via `mobile_codes.alpha2(...)[4]` and may be a list.
- `last_seen` from the API is UTC; `local_datetime()` converts it to the machine's
  local timezone for the printed table.
- `BM.json`, `a.json`, `b.json` are large downloaded data snapshots, not source.
- Output XML is import-only; CPS16 cannot paste XML, so this targets CPS2
  (radio firmware R2.10+).

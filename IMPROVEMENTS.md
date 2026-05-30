# zone.py — Proposed Improvements

Analysis of `zone.py` on `main`. Grouped by severity. This is a review backlog for
further inspection.

## Correctness bugs

### 1. Missing argument validation crashes with ugly tracebacks  ✅ DONE (branch claude-fixes)
`zone.py:23-34, 57-63`

`-t` is required but the parameter it depends on is not enforced:
- `-t mcc` without `-m` → `args.mcc` is `None` → line 128 `str(item['id']).startswith(None)` raises `TypeError`.
- `-t qth` without `-q` → line 58 `maidenhead.to_location(None)` errors.
- `-t gps` without `-lat`/`-lng` → `qth_coords = (None, None)` → `check_distance` errors.

Fix: a validation block (or argparse sub-parsers / custom check) that prints a clear
message and exits, instead of a stack trace.

### 2. No XML escaping  ✅ DONE (branch claude-fixes)
`zone.py:220-296`

`ch_alias`, `ch_cc`, `ch_rx`, `ch_tx` and city are interpolated raw into XML. A
callsign or city containing `&`, `<`, `>`, or `"` produces malformed XML that CPS2
will reject. City names with `&` are realistic in the BrandMeister data.

Fix: `xml.sax.saxutils.escape()` on interpolated values, or build XML with
`xml.etree.ElementTree`.

### 3. Unguarded coordinates in distance filter  ✅ DONE (branch claude-fixes)
`zone.py:134-135`

For `qth`/`gps`, `check_distance(qth_coords, (item['lat'], item['lng']))` assumes
every repeater has numeric coords. Entries with `null`/missing `lat`/`lng` will throw
inside geopy.

Fix: guard that skips coordinate-less repeaters.

## Robustness / performance

### 4. O(n^2) deduplication  ✅ DONE (branch claude-fixes)
`zone.py:152-154`

```python
if any((existing['rx'] == item['rx'] and ...) for existing in filtered_list):
```

Re-scans the entire `filtered_list` for every candidate. On the ~10 MB `BM.json`
(thousands of entries) it's noticeably slow. A `set` of `(rx, tx, callsign)` tuples
makes it O(n).

Bonus: the loop variable is also named `existing`, shadowing the global counter dict
on line 53. It happens to be safe (generator expressions have their own scope) but
it's confusing and a refactoring hazard.

### 5. Magic index into `mobile_codes`  ✅ DONE (branch claude-fixes)
`zone.py:62-63`

`mobile_codes.alpha2(args.mcc)[4]` relies on the namedtuple's positional layout, and
an invalid two-letter code throws an unhandled exception.

Fix: use the named field (`.mcc`) and catch the lookup failure with a friendly
"unknown country code" message.

## Code quality / maintainability

### 6. Import-time side effects
`zone.py:46-63`

Argument parsing and `qth_coords`/`mcc` computation run at module top level, so the
file can't be imported or tested without `sys.argv`. Moving this into `main()` would
make it testable.

### 7. Smaller items
- Bare `open`/`close` in `filter_list` (110, 162) and `write_zone_file` (301-303) — use `with`.
- `type(args.mcc) is list` (123) → `isinstance(args.mcc, list)`.
- `-zc 0` or negative → `range(..., 0)` raises `ValueError`; add a bounds check.
- Band detection via `rx.startswith('1')`/`'4'` (116-117) is crude but works for 2m/70cm; worth a comment.
- ✅ DONE (branch claude-fixes): warn when `BM.json` is more than 7 days old so users know to `-f`.

## Suggested priority order

1. **2 (XML escaping)** and **1 (arg validation)** — done.
2. **3** — data-dependent crash on coordinate-less repeaters.
3. **4** — performance + clarity cleanup.
4. **6** — larger refactor for a later pass.

## Notes / deliberate behavior (not bugs)

- `verify=False` on the BrandMeister download (`zone.py:82-84`) is **intentional** —
  the upstream API cert is the reason. Leave it as is.
- The simplex / TS1 / TS2 XML templates (`zone.py:224-296`) are **intentionally**
  separate, including `CP_ARSPLUS` only on the duplex blocks. Don't deduplicate them.

# zone.py — Proposed Improvements

Analysis of `zone.py` on `main`. Grouped by severity. No code changed yet — this is
a review backlog for further inspection.

## Correctness bugs

### 1. Missing argument validation crashes with ugly tracebacks
`zone.py:23-34, 57-63`

`-t` is required but the parameter it depends on is not enforced:
- `-t mcc` without `-m` → `args.mcc` is `None` → line 128 `str(item['id']).startswith(None)` raises `TypeError`.
- `-t qth` without `-q` → line 58 `maidenhead.to_location(None)` errors.
- `-t gps` without `-lat`/`-lng` → `qth_coords = (None, None)` → `check_distance` errors.

Fix: a validation block (or argparse sub-parsers / custom check) that prints a clear
message and exits, instead of a stack trace.

### 2. No XML escaping
`zone.py:220-296`

`ch_alias`, `ch_cc`, `ch_rx`, `ch_tx` and city are interpolated raw into XML. A
callsign or city containing `&`, `<`, `>`, or `"` produces malformed XML that CPS2
will reject. City names with `&` are realistic in the BrandMeister data.

Fix: `xml.sax.saxutils.escape()` on interpolated values, or build XML with
`xml.etree.ElementTree`.

### 3. Unguarded coordinates in distance filter
`zone.py:134-135`

For `qth`/`gps`, `check_distance(qth_coords, (item['lat'], item['lng']))` assumes
every repeater has numeric coords. Entries with `null`/missing `lat`/`lng` will throw
inside geopy.

Fix: guard that skips coordinate-less repeaters.

### 4. Suspicious `[:-1]` in callsign filter
`zone.py:144`

```python
if args.callsign and (not args.callsign in item['callsign'][:-1]):
```

The `[:-1]` strips the last character of the callsign before the substring match, so
the filter can never match against the final character. It also runs on the raw
callsign (before the `.split()[0]` on line 150), so it matches against trailing junk.
If the intent is "callsign contains this string," this looks like a bug.

ACTION: confirm whether the `[:-1]` is deliberate.

## Robustness / performance

### 5. O(n^2) deduplication
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

### 6. Magic index into `mobile_codes`
`zone.py:62-63`

`mobile_codes.alpha2(args.mcc)[4]` relies on the namedtuple's positional layout, and
an invalid two-letter code throws an unhandled exception.

Fix: use the named field (`.mcc`) and catch the lookup failure with a friendly
"unknown country code" message.

### 7. `verify=False` disables TLS verification
`zone.py:82-84`

Globally silences cert warnings and skips verification. If it's only needed for the
BM cert quirk, consider trying verified first and falling back, or at least
documenting why.

## Code quality / maintainability

### 8. ~90% duplicated XML templates
`zone.py:224-296`

The simplex, TS1, and TS2 blocks repeat nearly every field, and have already diverged:
`CP_ARSPLUS` is present in the duplex blocks but absent in the simplex one — is that
intentional? Parameterizing a single template (slot, alias suffix, optional ARS) would
shrink the file and prevent further drift.

### 9. Import-time side effects
`zone.py:46-63`

Argument parsing and `qth_coords`/`mcc` computation run at module top level, so the
file can't be imported or tested without `sys.argv`. Moving this into `main()` would
make it testable.

### 10. Smaller items
- Bare `open`/`close` in `filter_list` (110, 162) and `write_zone_file` (301-303) — use `with`.
- `type(args.mcc) is list` (123) → `isinstance(args.mcc, list)`.
- `-zc 0` or negative → `range(..., 0)` raises `ValueError`; add a bounds check.
- Band detection via `rx.startswith('1')`/`'4'` (116-117) is crude but works for 2m/70cm; worth a comment.
- Optional: warn when `BM.json` is stale (old mtime) so users know to `-f`.

## Suggested priority order

1. **2 (XML escaping)** and **1 (arg validation)** — cause silently broken output or crashes for normal usage.
2. **3** and **4** — data-dependent crashes / likely logic bug.
3. **5** — performance + clarity cleanup.
4. **8 / 9** — larger refactor for a later pass.
</content>

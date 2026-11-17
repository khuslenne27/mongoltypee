# Traditional Mongolian typing dictionary

This adapted subset is licensed CC BY-SA 4.0 (see LICENSE).
Attribution: Khudam contributors (https://github.com/bigune/khudam),
Wiktionary contributors (https://en.wiktionary.org/wiki/Wiktionary:Copyrights),
and the sources documented in the unchanged upstream SOURCES.md.
Exact upstream revision and adapted words.json SHA-256: upstream.json.

Selection/adaptations: include only `source: wiktionary` candidates and upstream
`verified: true` candidates. Exclude all unreviewed `wmk-import` conversions.
Keep 2–60-code-point single tokens in the traditional Mongolian alphabet,
preserving FVS, MVS, NNBSP, ZWJ and ZWNJ exactly. Exclude ordinary spaces,
punctuation, Latin letters, PUA and other scripts. Deduplicate by traditional
spelling, retaining all source references. Eight rejected candidates are recorded
unchanged in excluded.json for review; they are not imported.

Result: 1,504 distinct traditional spellings, of which one has upstream human
verification. The remaining entries are dictionary-backed, not locally reviewed.
This distinction is preserved in Word.verified. This is not official certification.

Run `python manage.py import_mongolian`, or `python manage.py setup_typing`.
Both use bundled files offline. Existing results and local human reviews survive
repeated imports. Admin can search by Cyrillic/traditional spelling and review
individual entries. Do not bulk mark the imported dictionary as human-verified.

The API serves this attributed dictionary pool for mn-Mong alongside locally
verified words. Sessions using the not-fully-reviewed pool are marked demo and
excluded from rankings; the UI labels them as dictionary-backed practice.
The original ten development examples are not part of this dictionary pool.

When distributing an adapted dictionary, retain attribution, indicate changes,
and distribute the adapted data under CC BY-SA 4.0. See LICENSE for full terms.

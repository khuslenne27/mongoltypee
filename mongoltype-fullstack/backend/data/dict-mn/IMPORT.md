# Bundled Cyrillic spelling dictionary

Source: https://github.com/bataak/dict-mn (Batmunkh Dorjgotov).
The exact upstream commit and dictionary SHA-256 are in `upstream.json`.
Original dictionary, affix rules, upstream README and MPL-2.0 license are
distributed unchanged. These data files retain their upstream license.

`python manage.py setup_typing` imports the bundled source without network access.
For an existing installation: `python manage.py import_dictionary`.
Imports are atomic and repeatable; existing test results are preserved.

Selection: unique NFC lowercase Cyrillic headwords, 2–16 letters, including ө/ү/ё.
Names, acronyms, punctuation, multiword entries, forbidden (`!!`), no-suggest (`--`),
and compound-only (`oc`) entries are excluded. Hunspell flags use `FLAG long`.
Affix combinations are not generated. No transliteration or spelling repairs
are applied. `verified=True` means dictionary-backed here, not government
certification or an independent human review by this project.

The original Cyrillic development examples are retired from the verified pool.
English remains the existing development pool. Traditional Mongolian examples
remain unverified and are not automatically served by the frontend. A reviewed,
appropriately licensed Traditional Mongolian source is still needed.

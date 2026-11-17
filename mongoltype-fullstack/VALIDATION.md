# Validation

2026-11-12 accounts: migration 0003 applied. CSRF-enforcing client tests cover
registration/password hashing, signed guest-history claiming, cross-device
history/progress, account-owned exercises, logout isolation and cookie rotation,
weak/duplicate credentials, login throttling, forged UUID ownership rejection,
cross-account exercise access and session/CSRF rotation. Authenticated exercise
POSTs require CSRF. Frontend TypeScript and production build passed for /login,
/register, account header and account-aware profile.

2026-11-12 Mongolian digits: backend language/category integration tests verify
Traditional Mongolian numbers/mixed use U+1810–U+1819 and saved results score
correctly; English/Cyrillic retain ASCII digits. Frontend keyboard tests cover
all ten digits in both layouts, physical number row/numpad, hints and unchanged
shifted punctuation. Number mapping is scoped to Mongolian numbers/mixed mode.

2026-11-12 vowel input: physical typing and screen keys share one CLDR layout
module. Five keyboard tests cover all seven vowels in both layouts, distinct
O/U and OE/UE code points, entry of all 1,504 dictionary spellings using the
indicated physical keys, selection/FVS correction, shortcut and IME pass-through.
Four feedback tests also pass. These are simulated key-event tests, not native
hardware/OS IME validation. Site keyboard mode is explicit and enabled by default.

2026-11-12 progress: 9 new tests cover exact settings and dictionary-status
separation, full-history personal best beyond 200 results, recent-five versus
previous-five comparisons, chronological chart data, empty/private history,
default selection, incomplete timed words, insertions/deletions and Mongolian
variation selectors. Frontend TypeScript and production build passed.

2026-11-11 save/replay integrity: Django migration 0002 applied. Regression
coverage checks start recovery without backdating, idempotent result retry,
signed-cookie ownership and forged UUID/cookie rejection, live timing/sequence
checks, paste/final-text mismatch rejection from rankings and legacy exclusion.
Frontend Attempt tests: `node --test --test-isolation=none lib/attempt.test.mjs`
(Node 24) cover rejected-start recovery, lost result responses, concurrent save,
session isolation and checkpoint coalescing. Practice results remain saveable
when the live checks are unavailable; these checks do not prove a human typed.

2026-11-11 dictionary integration: 10 Django test methods passed, Django system
check passed, frontend TypeScript and production build passed. Traditional
Mongolian import contains 1,504 distinct spellings from the pinned Khudam
Wiktionary/reviewed subset. Tests cover repeat import, preservation of local
human reviews and MVS code points, all four exercise categories, rejecting
unreviewed machine-source words from the pool, result/history persistence and
ranking exclusion. Browser/OS IME QA below is historical, not rerun for this change.

- Django: 6 test methods passed, including 12 language/category combinations, grapheme/FVS handling, word alignment, premature result rejection, visitor isolation, idempotent saves, duration validation and ranking exclusion of demo results.
- Django system checks passed.
- Next.js TypeScript check and production build passed.
- Chromium browser QA passed: horizontal and Mongolian vertical caret movement; unchanged text across typing; line/column scrolling; Backspace scroll return; 10-word completion; Django result save and profile history; 15-second timer completion; mixed category; mobile widths on all three routes.
- Keyboard QA passed: clickable key input, physical key highlight, Shift alternate letter layer, mobile width.
- Screenshot inspection: Mongolian text, keyboard, controls, profile layout.

Not yet verified: native Windows/macOS IME hardware end-to-end, Firefox/Safari shaping differences, PostgreSQL runtime (automated checks used SQLite). The keyboard represents the selected Windows layout; it does not auto-detect the OS keyboard.

V2.1: Chromium verified immediate green/red glyph feedback, unchanged text when pressing space, unchanged scroll within a column, and movement after column completion. Clean production build passed.

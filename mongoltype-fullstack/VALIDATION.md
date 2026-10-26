# Validation
- Django: 6 test methods passed, including 12 language/category combinations, grapheme/FVS handling, word alignment, premature result rejection, visitor isolation, idempotent saves, duration validation and ranking exclusion of demo results.
- Django system checks passed.
- Next.js TypeScript check and production build passed.
- Chromium browser QA passed: horizontal and Mongolian vertical caret movement; unchanged text across typing; line/column scrolling; Backspace scroll return; 10-word completion; Django result save and profile history; 15-second timer completion; mixed category; mobile widths on all three routes.
- Keyboard QA passed: clickable key input, physical key highlight, Shift alternate letter layer, mobile width.
- Screenshot inspection: Mongolian text, keyboard, controls, profile layout.

Not yet verified: native Windows/macOS IME hardware end-to-end, Firefox/Safari shaping differences, PostgreSQL runtime (automated checks used SQLite). The keyboard represents the selected Windows layout; it does not auto-detect the OS keyboard.

V2.1: Chromium verified immediate green/red glyph feedback, unchanged text when pressing space, unchanged scroll within a column, and movement after column completion. Clean production build passed.

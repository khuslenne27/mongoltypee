"""Typing-safe standalone headwords from the bundled dict-mn Hunspell source."""
import re
import unicodedata


def headwords(lines):
    seen = set()
    for line in lines:
        entry = line.strip()
        if not entry or entry.startswith('#') or entry.isdigit():
            continue
        token = entry.split()[0]
        word, _, encoded_flags = token.partition('/')
        flags = {encoded_flags[i:i + 2] for i in range(0, len(encoded_flags), 2)}
        # FLAG long; exclude forbidden, no-suggest and compound-only entries.
        if flags & {'!!', '--', 'oc'}:
            continue
        word = unicodedata.normalize('NFC', word)
        # Preserve spelling: exclude names/acronyms rather than lowercasing them.
        if not re.fullmatch('[а-яёөү]{2,16}', word) or word in seen:
            continue
        seen.add(word)
        yield word

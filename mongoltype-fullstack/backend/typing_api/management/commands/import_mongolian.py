"""Import the attributed Wiktionary subset without promoting review status."""
import hashlib
import json
import re

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from typing_api.models import Word

SOURCE_PREFIX = 'Khudam/Wiktionary | '


class Command(BaseCommand):
    help = 'Import bundled Traditional Mongolian dictionary words (offline, repeatable).'

    def handle(self, *args, **options):
        directory = settings.BASE_DIR / 'data' / 'khudam'
        metadata = json.loads((directory / 'upstream.json').read_text(encoding='utf-8'))
        raw = (directory / 'words.json').read_bytes()
        if hashlib.sha256(raw).hexdigest() != metadata['sha256']:
            raise CommandError('Traditional Mongolian dictionary checksum mismatch.')
        rows = json.loads(raw)
        # Validate the entire input before writing. Preserve FVS/MVS/NNBSP/ZWJ.
        for row in rows:
            if not re.fullmatch(r'[\u1820-\u1842][\u1820-\u1842\u180b-\u180f\u200c\u200d\u202f]{1,59}', row['text']):
                raise CommandError('Invalid Traditional Mongolian dictionary token.')
            if not row['references'] or (any(
                ref['source'] != 'wiktionary' for ref in row['references']
            ) and row['verified'] is not True):
                raise CommandError('Unreviewed machine-converted candidate is not allowed.')
        provenance = SOURCE_PREFIX + f"{metadata['repository']}/tree/{metadata['commit']} | CC-BY-SA-4.0"
        with transaction.atomic():
            for row in rows:
                word, created = Word.objects.get_or_create(
                    language='mn-Mong', text=row['text'],
                    defaults={'cyrillic': row['cyrillic'], 'verified': row['verified'], 'source': provenance},
                )
                if not created and (word.source.startswith(SOURCE_PREFIX) or
                                    word.source.startswith('Development examples')):
                    word.cyrillic = row['cyrillic']
                    # Never undo a local human review on repeated import.
                    word.verified = word.verified or row['verified']
                    word.source = provenance
                    word.save(update_fields=['cyrillic', 'verified', 'source'])
        reviewed = sum(row['verified'] for row in rows)
        self.stdout.write(self.style.SUCCESS(
            f'Imported {len(rows)} Traditional Mongolian dictionary words ({reviewed} upstream human-reviewed).'
        ))

import hashlib
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from typing_api.dictionary import headwords
from typing_api.models import Word


class Command(BaseCommand):
    help = 'Import the pinned, bundled dict-mn Cyrillic spelling dictionary (offline).'

    def handle(self, *args, **options):
        directory = settings.BASE_DIR / 'data' / 'dict-mn'
        metadata = json.loads((directory / 'upstream.json').read_text(encoding='utf-8'))
        dictionary = directory / 'mn_MN.dic'
        if hashlib.sha256(dictionary.read_bytes()).hexdigest() != metadata['sha256']:
            raise CommandError('Dictionary checksum mismatch; restore the pinned source.')
        with dictionary.open(encoding='utf-8-sig') as source:
            words = list(headwords(source))
        if not words:
            raise CommandError('No suitable dictionary words found.')
        provenance = f"{metadata['repository']}/tree/{metadata['commit']} | MPL-2.0"
        with transaction.atomic():
            # Keep old test sessions/results; retire the original development pool.
            Word.objects.filter(language='mn-Cyrl', source__startswith='Development examples').update(verified=False)
            Word.objects.bulk_create(
                [Word(language='mn-Cyrl', text=word, verified=True, source=provenance) for word in words],
                ignore_conflicts=True, batch_size=500,
            )
            # Existing matching rows must also acquire the dictionary provenance.
            for offset in range(0, len(words), 500):
                Word.objects.filter(language='mn-Cyrl', text__in=words[offset:offset + 500]).update(
                    verified=True, source=provenance,
                )
        self.stdout.write(self.style.SUCCESS(f'Imported {len(words)} dictionary-backed Cyrillic words.'))

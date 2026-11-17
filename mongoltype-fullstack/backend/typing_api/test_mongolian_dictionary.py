from django.contrib.auth import get_user_model
import json
import uuid
from datetime import timedelta
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from .models import TestSession, Word


class MongolianDictionaryTests(TestCase):
    def test_import_preserves_source_review_status_and_local_reviews(self):
        call_command('import_mongolian', stdout=StringIO())
        imported = Word.objects.filter(language='mn-Mong', source__startswith='Khudam/Wiktionary | ')
        self.assertEqual(imported.count(), 1504)
        self.assertEqual(imported.filter(verified=True).count(), 1)
        rows = json.loads((settings.BASE_DIR / 'data/khudam/words.json').read_text(encoding='utf-8'))
        for row in rows:
            self.assertTrue(row['verified'] or all(ref['source'] == 'wiktionary' for ref in row['references']))
        # No normalization or invisible-letter stripping during import.
        shaped = next(row for row in rows if '\u180e' in row['text'])
        self.assertTrue(imported.filter(text=shaped['text']).exists())
        reviewed = imported.filter(verified=False).first()
        reviewed.verified = True
        reviewed.save()
        call_command('import_mongolian', stdout=StringIO())
        self.assertEqual(imported.count(), 1504)
        reviewed.refresh_from_db()
        self.assertTrue(reviewed.verified)

    def test_dictionary_served_without_demo_opt_in_and_excluded_from_ranking(self):
        self.client.force_login(get_user_model().objects.create_user(username="mongolreader"))
        call_command('import_mongolian', stdout=StringIO())
        Word.objects.create(language='mn-Mong', text='ᠠᠠᠠᠠᠠ', source='Unreviewed machine conversion')
        headers = {'HTTP_X_VISITOR_ID': str(uuid.uuid4())}
        for category in ['words', 'punctuation', 'numbers', 'mixed']:
            response = self.client.post('/api/tests', {
                'language': 'mn-Mong', 'mode': 'words', 'category': category,
                'amount': 10, 'demo': False,
            }, content_type='application/json', **headers)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['corpus'], 'dictionary')
            self.assertTrue(data['demo'])
            self.assertNotIn('ᠠᠠᠠᠠᠠ', data['text'])
            for token in data['text'].split(' '):
                word = token.rstrip('᠂᠃᠄᠁')
                if not word.isdigit():
                    self.assertTrue(Word.objects.filter(language='mn-Mong', text=word,
                                                       source__startswith='Khudam/Wiktionary | ').exists())
        test = self.client.post('/api/tests', {
            'language': 'mn-Mong', 'mode': 'time', 'category': 'words', 'amount': 30,
        }, content_type='application/json', **headers).json()
        TestSession.objects.filter(id=test['id']).update(started_at=timezone.now() - timedelta(seconds=30))
        saved = self.client.post('/api/results', {
            'session_id': test['id'], 'typed_text': test['text'].split(' ')[0], 'elapsed_ms': 30000,
        }, content_type='application/json', **headers)
        self.assertEqual(saved.status_code, 201)
        self.assertEqual(len(self.client.get('/api/history', **headers).json()), 1)
        self.assertEqual(self.client.get('/api/leaderboard?language=mn-Mong').json(), [])

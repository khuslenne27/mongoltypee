from io import StringIO

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from .dictionary import headwords
from .models import Word


class DictionaryParserTests(SimpleTestCase):
    def test_only_standalone_lowercase_cyrillic_words(self):
        entries = ['12', '# comment', 'ном/B10B', 'ном', 'Монгол/B1',
                   'муу/!!', 'өөр/oc', 'үсэг/--', 'ус/A00A',
                   'abc', 'хоёр-үг', 'нэг үг', 'а']
        self.assertEqual(list(headwords(entries)), ['ном', 'ус', 'нэг'])


class DictionaryImportTests(TestCase):
    def test_bundled_import_is_repeatable_and_used_by_tests(self):
        Word.objects.create(language='mn-Cyrl', text='хуучинжишээ', verified=True,
                            source='Development examples; review Mongolian script before production')
        output = StringIO()
        call_command('import_dictionary', stdout=output)
        count = Word.objects.filter(language='mn-Cyrl', verified=True).count()
        self.assertGreater(count, 10000)
        self.assertFalse(Word.objects.get(text='хуучинжишээ').verified)
        self.assertTrue(Word.objects.get(language='mn-Cyrl', text='ном').verified)
        call_command('import_dictionary', stdout=output)
        self.assertEqual(Word.objects.filter(language='mn-Cyrl', verified=True).count(), count)
        import uuid
        response = self.client.post('/api/tests', {
            'language': 'mn-Cyrl', 'mode': 'words', 'amount': 10, 'category': 'words',
        }, content_type='application/json', HTTP_X_VISITOR_ID=str(uuid.uuid4()))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['demo'])
        for word in response.json()['text'].split(' '):
            self.assertTrue(Word.objects.filter(text=word, language='mn-Cyrl', verified=True,
                                               source__contains='bataak/dict-mn').exists())

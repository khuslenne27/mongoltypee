from django.contrib.auth import get_user_model
import uuid
from datetime import timedelta

from django.core.cache import cache
from django.test import Client, SimpleTestCase, TestCase
from django.utils import timezone

from .models import Result, TestSession
from .progress import mistakes


class MistakeTests(SimpleTestCase):
    def test_untouched_tail_and_unfinished_last_word_are_not_errors(self):
        letters, words = mistakes('book water school', 'book wa', True)
        self.assertFalse(letters)
        self.assertFalse(words)

    def test_skipped_and_deleted_letters_in_committed_words_are_counted(self):
        letters, words = mistakes('book water school', 'bok  sc', True)
        self.assertEqual(letters['o'], 1)
        self.assertEqual(words['book'], 1)
        self.assertEqual(words['water'], 1)
        self.assertNotIn('school', words)

    def test_mongolian_variation_selector_is_one_grapheme(self):
        letters, words = mistakes('ᠠ\u180b ᠨᠣᠮ', 'ᠠ ', True)
        self.assertEqual(letters['ᠠ\u180b'], 1)
        self.assertEqual(words['ᠠ\u180b'], 1)
        self.assertNotIn('ᠨᠣᠮ', words)

    def test_insertions_mark_the_word_without_shifting_all_later_letters(self):
        letters, words = mistakes('book water', 'boook water', False)
        self.assertFalse(letters)
        self.assertEqual(words['book'], 1)
        self.assertNotIn('water', words)


class ProgressTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(username="testreader")
        self.client.force_login(self.user)
        self.visitor = uuid.uuid4()
        self.headers = {'HTTP_X_VISITOR_ID': str(self.visitor)}

    def add(self, speed, **settings):
        session = TestSession.objects.create(user=self.user, visitor=self.visitor, language='en', mode='time',
                                            category='words', amount=30, text='book water school')
        for field, value in settings.items():
            setattr(session, field, value)
        session.save()
        return Result.objects.create(session=session, typed_text='bok water', elapsed_ms=30000,
                                     wpm=speed, accuracy=90, errors=1)

    def query(self, **settings):
        return self.client.get('/api/progress', {'language': 'en', 'mode': 'time', 'category': 'words',
                                               'amount': 30, 'demo': 'false', **settings}, **self.headers)

    def test_exact_settings_separate_duration_and_dictionary_status(self):
        self.add(20)
        self.add(40)
        self.add(200, amount=15)
        self.add(300, demo=True)
        self.add(400, category='mixed')
        data = self.query().json()
        self.assertEqual(data['summary']['count'], 2)
        self.assertEqual(data['summary']['average_wpm'], 30)
        self.assertEqual(data['summary']['best']['wpm'], 40)
        self.assertEqual(data['summary']['latest_delta'], 20)
        self.assertEqual(len(data['groups']), 4)
        self.assertEqual(data['words'][0], {'text': 'book', 'count': 2})

    def test_full_history_best_not_limited_to_recent_200(self):
        best = self.add(150)
        Result.objects.filter(pk=best.pk).update(created_at=timezone.now() - timedelta(days=100))
        for _ in range(201):
            self.add(20)
        data = self.query().json()
        self.assertEqual(data['summary']['count'], 202)
        self.assertEqual(data['summary']['best']['id'], best.id)
        self.assertEqual(len(data['history']), 50)
        self.assertEqual(len(data['recent']), 10)
        self.assertEqual(data['words'][0]['count'], 202)

    def test_recent_five_compared_to_previous_five(self):
        for speed in [10] * 5 + [20] * 5:
            self.add(speed)
        data = self.query().json()
        self.assertEqual(data['comparison'], {'current': 20, 'previous': 10, 'delta': 10})
        self.assertEqual([row['wpm'] for row in data['recent']], [10] * 5 + [20] * 5)

    def test_empty_and_other_visitor_history_are_private(self):
        self.add(50)
        other = Client()
        self.assertEqual(other.get("/api/progress").status_code, 403)
        other.force_login(get_user_model().objects.create_user(username="otherreader"))
        data = other.get('/api/progress', HTTP_X_VISITOR_ID=str(uuid.uuid4())).json()
        self.assertEqual(data['groups'], [])
        self.assertIsNone(data['summary'])
        self.assertEqual(self.query(language='invalid').status_code, 400)

    def test_default_selects_latest_configuration(self):
        self.add(50)
        self.add(30, mode='words', amount=10)
        data = self.client.get('/api/progress', **self.headers).json()
        self.assertEqual(data['selected']['mode'], 'words')
        self.assertEqual(data['selected']['amount'], 10)
        self.assertIsNone(data['summary']['latest_delta'])
        self.assertIsNone(data['comparison'])

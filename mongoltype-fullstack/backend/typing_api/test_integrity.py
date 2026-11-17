from django.contrib.auth import get_user_model
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.test import Client, TestCase
from django.utils import timezone
from django.core.cache import cache

from .models import Result, TestSession, Word


class IntegrityTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(username="testreader")
        self.client.force_login(self.user)
        Word.objects.create(language='en', text='book', verified=True)
        self.t0 = timezone.now()
        self.test = self.client.post('/api/tests', {
            'language': 'en', 'mode': 'time', 'category': 'words', 'amount': 30,
        }, content_type='application/json').json()
        self.pk = self.test['id']
        with patch('typing_api.views.timezone.now', return_value=self.t0):
            self.client.post(f'/api/tests/{self.pk}/start', {}, content_type='application/json')

    def post_checkpoint(self, seq, text, second):
        with patch('typing_api.live.timezone.now', return_value=self.t0 + timedelta(seconds=second)):
            return self.client.post(f'/api/tests/{self.pk}/checkpoint', {
                'seq': seq, 'typed_text': text,
            }, content_type='application/json')

    def tearDown(self):
        cache.clear()

    def stream(self, start=1):
        text = ''
        for seq in range(start, 31):
            text = ('book ' * seq).rstrip()
            self.assertEqual(self.post_checkpoint(seq, text, seq).status_code, 200)
        return text

    def save(self, text, elapsed=30000):
        with patch('typing_api.views.timezone.now', return_value=self.t0 + timedelta(seconds=31)):
            return self.client.post('/api/results', {
                'session_id': self.pk, 'typed_text': text, 'elapsed_ms': elapsed,
            }, content_type='application/json')

    def test_live_result_ranks_using_server_duration_and_is_idempotent(self):
        text = self.stream()
        response = self.save(text, 29900)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['rank_eligible'])
        self.assertEqual(response.json()['elapsed_ms'], 30000)
        repeat = self.save(text)
        self.assertEqual(repeat.status_code, 200)
        self.assertEqual(repeat.json()['id'], response.json()['id'])
        self.assertEqual(Result.objects.count(), 1)
        self.assertEqual(len(self.client.get('/api/leaderboard?language=en').json()), 1)

    def test_final_text_only_cannot_rank(self):
        response = self.save('book')
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.json()['rank_eligible'])
        self.assertEqual(self.client.get('/api/leaderboard?language=en').json(), [])

    def test_bulk_paste_or_missing_checkpoints_cannot_rank(self):
        self.post_checkpoint(1, 'book ' * 100, 1)
        text = self.stream(start=2)
        self.assertFalse(self.save(text).json()['rank_eligible'])

    def test_final_text_mismatch_cannot_rank(self):
        text = self.stream()
        self.assertFalse(self.save(text + ' book').json()['rank_eligible'])

    def test_uuid_header_and_tampered_cookie_cannot_access_new_session(self):
        session = TestSession.objects.get(pk=self.pk)
        attacker = Client()
        headers = {'HTTP_X_VISITOR_ID': str(session.visitor)}
        self.assertEqual(attacker.post(f'/api/tests/{self.pk}/start', {}, content_type='application/json', **headers).status_code, 404)
        attacker.cookies['mongoltype-browser'] = str(session.visitor) + ':forged'
        self.assertEqual(attacker.post(f'/api/tests/{self.pk}/checkpoint', {
            'seq': 1, 'typed_text': 'book',
        }, content_type='application/json', **headers).status_code, 404)
        self.assertEqual(attacker.get('/api/history', **headers).status_code, 403)

    def test_lost_start_recovery_saves_practice_without_backdating_clock(self):
        TestSession.objects.filter(pk=self.pk).update(started_at=None)
        response = self.client.post(f'/api/tests/{self.pk}/start', {'recover': True}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        session = TestSession.objects.get(pk=self.pk)
        started = session.started_at
        self.assertTrue(session.recovered_start)
        response = self.save('book')
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.json()['rank_eligible'])
        self.client.post(f'/api/tests/{self.pk}/start', {}, content_type='application/json')
        session.refresh_from_db()
        self.assertEqual(session.started_at, started)
        self.assertTrue(session.recovered_start)

    def test_out_of_order_and_late_checkpoints_cannot_restore_integrity(self):
        self.post_checkpoint(2, 'book', 5)
        session = TestSession.objects.get(pk=self.pk)
        self.assertFalse(session.integrity_ok)
        self.assertEqual(self.post_checkpoint(1, 'book', 6).status_code, 409)
        self.post_checkpoint(3, 'book book', 33)
        self.assertFalse(self.save('book book').json()['rank_eligible'])

    def test_early_result_is_rejected_even_if_client_claims_thirty_seconds(self):
        with patch('typing_api.views.timezone.now', return_value=self.t0 + timedelta(seconds=1)):
            response = self.client.post('/api/results', {
                'session_id': self.pk, 'typed_text': 'book', 'elapsed_ms': 30000,
            }, content_type='application/json')
        self.assertEqual(response.status_code, 400)

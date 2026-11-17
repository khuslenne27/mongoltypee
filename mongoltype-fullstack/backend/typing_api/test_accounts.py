import uuid
from datetime import timedelta
from django.utils import timezone

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings

from .models import Result, TestSession, Word


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AccountTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client(enforce_csrf_checks=True)
        Word.objects.create(language='en', text='book', verified=True)
        self.password = 'River-Garden-83!'

    def post(self, path, data, client=None):
        client = client or self.client
        token = client.get('/api/auth/me').json()['csrf_token']
        return client.post(path, data, content_type='application/json', HTTP_X_CSRFTOKEN=token)

    def register(self, username='writer', client=None):
        return self.post('/api/auth/register', {'username': username, 'password': self.password}, client)

    def guest_result(self, client=None):
        client = client or self.client
        test = self.post('/api/tests', {'language': 'en', 'mode': 'words', 'amount': 10, 'category': 'words'}, client).json()
        session = TestSession.objects.get(pk=test['id'])
        Result.objects.create(session=session, typed_text=session.text, elapsed_ms=30000, wpm=20, accuracy=100, errors=0)
        return session

    def test_registration_hashes_password_and_claims_only_signed_guest_history(self):
        session = self.guest_result()
        other = TestSession.objects.create(visitor=uuid.uuid4(), language='en', text='book', browser_owned=True)
        response = self.register('Writer')
        self.assertEqual(response.status_code, 201, response.content)
        user = get_user_model().objects.get(username='writer')
        self.assertNotEqual(user.password, self.password)
        self.assertTrue(user.check_password(self.password))
        session.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(session.user, user)
        self.assertIsNone(other.user)
        self.assertEqual(len(self.client.get('/api/history').json()), 1)
        self.assertEqual(self.client.get('/api/auth/me').json()['user']['username'], 'writer')

    def test_login_on_second_device_sees_history_and_new_tests_belong_to_account(self):
        self.guest_result()
        self.register()
        second = Client(enforce_csrf_checks=True)
        response = self.post('/api/auth/login', {'username': 'WRITER', 'password': self.password}, second)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(second.get('/api/history').json()), 1)
        self.assertEqual(second.get('/api/progress').json()['summary']['count'], 1)
        created = self.post('/api/tests', {'language': 'en', 'mode': 'words', 'amount': 10, 'category': 'words'}, second)
        self.assertEqual(created.status_code, 200)
        self.assertEqual(TestSession.objects.get(pk=created.json()['id']).user.username, 'writer')

    def test_csrf_required_for_registration_login_logout_and_authenticated_typing(self):
        data = {'username': 'writer', 'password': self.password}
        for path in ['/api/auth/register', '/api/auth/login', '/api/auth/logout']:
            self.assertEqual(self.client.post(path, data, content_type='application/json').status_code, 403)
        self.register()
        response = self.client.post('/api/tests', {'language': 'en', 'mode': 'time', 'amount': 30, 'category': 'words'}, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.post('/api/auth/logout', {}).status_code, 200)
        self.assertIsNone(self.client.get('/api/auth/me').json()['user'])

    def test_logout_hides_account_history_and_prevents_second_account_takeover(self):
        session = self.guest_result()
        self.register()
        cookie = self.client.cookies['mongoltype-browser'].value
        self.post('/api/auth/logout', {})
        self.assertEqual(self.client.get('/api/history').status_code, 403)
        self.assertNotEqual(self.client.cookies['mongoltype-browser'].value, cookie)
        self.register('otherwriter')
        self.assertEqual(self.client.get('/api/history').json(), [])
        session.refresh_from_db()
        self.assertEqual(session.user.username, 'writer')
        attacker = Client()
        attacker.cookies['mongoltype-browser'] = cookie
        self.assertEqual(attacker.get('/api/history').status_code, 403)

    def test_invalid_password_duplicate_username_and_weak_password(self):
        self.register()
        self.post('/api/auth/logout', {})
        self.assertEqual(self.post('/api/auth/login', {'username': 'writer', 'password': 'wrong'}).status_code, 400)
        self.assertEqual(self.register('WRITER').status_code, 409)
        self.assertEqual(self.post('/api/auth/register', {'username': 'newwriter', 'password': '12345678'}).status_code, 400)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_uuid_header_cannot_claim_another_guests_history(self):
        session = self.guest_result()
        second = Client(enforce_csrf_checks=True)
        token = second.get('/api/auth/me').json()['csrf_token']
        response = second.post('/api/auth/register', {'username': 'second', 'password': self.password},
                               content_type='application/json', HTTP_X_CSRFTOKEN=token, HTTP_X_VISITOR_ID=str(session.visitor))
        self.assertEqual(response.status_code, 201)
        session.refresh_from_db()
        self.assertIsNone(session.user)
        self.assertEqual(second.get('/api/history').json(), [])

    def test_login_attempts_are_rate_limited(self):
        for _ in range(10):
            self.post('/api/auth/login', {'username': 'missing', 'password': self.password})
        self.assertEqual(self.post('/api/auth/login', {'username': 'missing', 'password': self.password}).status_code, 429)

    def test_authenticated_user_cannot_mutate_another_users_attempt(self):
        session = self.guest_result()
        self.register()
        second = Client(enforce_csrf_checks=True)
        self.register('second', second)
        self.assertEqual(self.post(f'/api/tests/{session.id}/start', {}, second).status_code, 404)
        self.assertEqual(self.post(f'/api/tests/{session.id}/checkpoint', {'seq': 1, 'typed_text': 'book'}, second).status_code, 404)

    def test_login_rotates_session_and_csrf_tokens(self):
        self.register()
        first = self.client.cookies['sessionid'].value
        self.post('/api/auth/logout', {})
        old_token = self.client.get('/api/auth/me').json()['csrf_token']
        self.post('/api/auth/login', {'username': 'writer', 'password': self.password})
        self.assertNotEqual(self.client.cookies['sessionid'].value, first)
        self.assertEqual(self.client.post('/api/auth/logout', {}, content_type='application/json', HTTP_X_CSRFTOKEN=old_token).status_code, 403)

    def test_leaderboard_combines_devices_for_one_account(self):
        user = get_user_model().objects.create_user(username='rankedwriter', password=self.password)
        for speed in [20, 40]:
            session = TestSession.objects.create(user=user, visitor=uuid.uuid4(), language='en', mode='time',
                                                category='words', amount=30, browser_owned=True, text='book')
            Result.objects.create(session=session, typed_text='book', elapsed_ms=30000, wpm=speed,
                                  accuracy=100, errors=0, rank_eligible=True)
        self.client.force_login(user)
        data = self.client.get('/api/leaderboard?language=en').json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'rankedwriter')
        self.assertEqual(data[0]['speed'], 40)
        self.assertEqual(data[0]['tests'], 2)

    def test_frontend_identity_bootstrap_before_and_after_login(self):
        for signed_in in [False, True]:
            if signed_in:
                self.register()
            response = self.post('/api/identity', {})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()['csrf_token'])
            self.assertTrue(self.client.cookies['mongoltype-browser']['httponly'])

    def test_guests_can_type_but_private_history_progress_and_ranking_require_login(self):
        response = self.post('/api/tests', {'language': 'en', 'mode': 'words', 'amount': 10, 'category': 'words'})
        self.assertEqual(response.status_code, 200)
        test = response.json()
        self.assertEqual(self.post(f"/api/tests/{test['id']}/start", {}).status_code, 200)
        TestSession.objects.filter(pk=test['id']).update(started_at=timezone.now() - timedelta(seconds=1))
        saved = self.post('/api/results', {'session_id': test['id'], 'typed_text': test['text'], 'elapsed_ms': 1000})
        self.assertEqual(saved.status_code, 201)
        for path in ['/api/history', '/api/progress', '/api/leaderboard']:
            self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(len(self.client.get('/api/history').json()), 1)
        self.assertEqual(self.client.get('/api/progress').json()['summary']['count'], 1)
        self.assertEqual(self.client.get('/api/leaderboard').status_code, 200)

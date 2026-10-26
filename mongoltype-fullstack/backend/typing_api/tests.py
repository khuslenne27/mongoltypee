import uuid
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from .models import Word,TestSession
from .scoring import score
class TypingTests(TestCase):
    def setUp(self):
        self.visitor=str(uuid.uuid4());self.headers={'HTTP_X_VISITOR_ID':self.visitor}
        for lang,text in [('en','book'),('mn-Cyrl','ном'),('mn-Mong','ᠨᠣᠮ')]:Word.objects.create(language=lang,text=text,verified=lang!='mn-Mong')
    def new(self,**kwargs):
        return self.client.post('/api/tests',{'language':'en','mode':'words','amount':10,'category':'words',**kwargs},content_type='application/json',**self.headers)
    def submit(self,test,text,ms=1000):
        self.client.post(f"/api/tests/{test['id']}/start",{},content_type='application/json',**self.headers)
        TestSession.objects.filter(id=test['id']).update(started_at=timezone.now()-timedelta(milliseconds=ms))
        return self.client.post('/api/results',{'session_id':test['id'],'typed_text':text,'elapsed_ms':ms},content_type='application/json',**self.headers)
    def test_word_modes_and_categories_all_languages(self):
        for language in ['en','mn-Cyrl','mn-Mong']:
            for category in ['words','punctuation','numbers','mixed']:
                r=self.new(language=language,category=category,demo=True);self.assertEqual(r.status_code,200)
                test=r.json();self.assertEqual(len(test['text'].split(' ')),10)
                if category in ['numbers','mixed']:self.assertTrue(any(c.isdigit() for c in test['text']))
                if category in ['punctuation','mixed']:self.assertTrue(any(c in ',.!?;᠂᠃᠄᠁' for c in test['text']))
                saved=self.submit(test,test['text']);self.assertEqual(saved.status_code,201,saved.content);self.assertEqual(saved.json()['accuracy'],100)
    def test_unicode_selector_and_word_alignment(self):
        self.assertEqual(score('ᠠ\u180b','ᠠ\u180b',60000)['wpm'],.2)
        self.assertEqual(score('ᠠ\u180b','ᠠ',60000)['errors'],1)
        self.assertEqual(score('book water','bookk water',60000)['errors'],1)
    def test_incomplete_and_early_time_rejected(self):
        t=self.new().json();self.assertEqual(self.submit(t,'book').status_code,400)
        t=self.new(mode='time',amount=15).json();self.assertEqual(self.submit(t,'book').status_code,400)
    def test_result_history_isolation_and_idempotent(self):
        t=self.new().json();first=self.submit(t,t['text']);self.assertEqual(first.status_code,201)
        repeat=self.submit(t,t['text']);self.assertEqual(repeat.status_code,200);self.assertEqual(first.json()['id'],repeat.json()['id'])
        self.assertEqual(len(self.client.get('/api/history',**self.headers).json()),1)
        self.assertEqual(self.client.get('/api/history',HTTP_X_VISITOR_ID=str(uuid.uuid4())).json(),[])
        self.assertEqual(self.client.post(f"/api/tests/{t['id']}/start",{},content_type='application/json',HTTP_X_VISITOR_ID=str(uuid.uuid4())).status_code,404)
    def test_demo_and_invalid_options(self):
        self.assertEqual(self.new(language='mn-Mong').status_code,503)
        self.assertTrue(self.new(language='mn-Mong',demo=True).json()['demo'])
        self.assertEqual(self.new(amount=11).status_code,400)
        self.assertEqual(self.new(mode='time',amount=120).status_code,200)
        self.assertEqual(self.new(category='bad').status_code,400)
    def test_timer_save_and_demo_excluded_from_ranking(self):
        t=self.new(mode='time',amount=30).json();r=self.submit(t,'book',30000);self.assertEqual(r.status_code,201)
        self.assertEqual(len(self.client.get('/api/leaderboard?language=en').json()),1)
        t=self.new(mode='time',amount=30,language='mn-Mong',demo=True).json();self.submit(t,'ᠨᠣᠮ',30000)
        self.assertEqual(self.client.get('/api/leaderboard?language=mn-Mong').json(),[])

import random
import secrets
from uuid import UUID, uuid4
from django.conf import settings
from django.core.signing import BadSignature
from django.middleware.csrf import get_token
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from .models import Word,TestSession,Result
from .scoring import score,completed,units
LANGUAGES=['en','mn-Cyrl','mn-Mong']
COOKIE='mongoltype-browser'

def browser_id(request):
    try:return UUID(request.get_signed_cookie(COOKIE,salt=COOKIE,max_age=31536000))
    except (KeyError,BadSignature,ValueError):return None

def visitor(request):
    signed=browser_id(request)
    if signed:return signed
    try: return UUID(request.headers.get('X-Visitor-ID',''))
    except (ValueError,AttributeError): raise serializers.ValidationError({'detail':'Missing visitor identifier'})
def owned(request,pk):
    try: return sessions_for(request).get(id=pk)
    except (TestSession.DoesNotExist,ValueError): return None
def sessions_for(request):
    if request.user.is_authenticated:return TestSession.objects.filter(user=request.user)
    signed=browser_id(request)
    if signed:return TestSession.objects.filter(visitor=signed,browser_owned=True,user__isnull=True)
    return TestSession.objects.filter(visitor=visitor(request),browser_owned=False,user__isnull=True)

class NewInput(serializers.Serializer):
    language=serializers.ChoiceField(choices=LANGUAGES)
    mode=serializers.ChoiceField(choices=['time','words'])
    category=serializers.ChoiceField(choices=['words','punctuation','numbers','mixed'])
    amount=serializers.IntegerField(min_value=1,max_value=200)
    demo=serializers.BooleanField(default=False)

@api_view(['POST'])
def identity(request):
    response=Response({'ready':True,'csrf_token':get_token(request)})
    response.set_signed_cookie(COOKIE,str(browser_id(request) or uuid4()),salt=COOKIE,max_age=31536000,
                               httponly=True,secure=not settings.DEBUG,samesite='Strict')
    return response
@api_view(['POST'])
def new_test(request):
    v=browser_id(request) or uuid4(); serializer=NewInput(data=request.data);serializer.is_valid(raise_exception=True);data=serializer.validated_data
    valid=[15,30,60,120] if data['mode']=='time' else [10,25,50,100]
    if data['amount'] not in valid:return Response({'detail':'Invalid amount'},status=400)
    corpus='reviewed'
    words=Word.objects.filter(language=data['language'],verified=True)
    if data['language']=='mn-Mong':
        # Dictionary-backed practice is allowed; it does not imply human approval.
        words=Word.objects.filter(language='mn-Mong').filter(Q(verified=True)|Q(source__startswith='Khudam/Wiktionary | '))
        if words.filter(verified=False).exists():corpus='dictionary'
    pool=list(words.values_list('text',flat=True));demo=corpus=='dictionary'
    if not pool and data['demo']:
        pool=list(Word.objects.filter(language=data['language']).values_list('text',flat=True));demo=bool(pool)
        corpus='demo'
    if not pool:return Response({'detail':'Энэ хэлний хянагдсан үгийн сан хараахан ороогүй байна. Өөр хэл сонгоно уу.'},status=503)
    count=600 if data['mode']=='time' else data['amount']; selected=[]
    punctuation=['᠂','᠃','᠄','᠁'] if data['language']=='mn-Mong' else [',','.','!','?',';']
    for i in range(count):
        word=secrets.choice(pool)
        while len(pool)>1 and selected and word==selected[-1]:word=secrets.choice(pool)
        # Every third token gets a number; every second token gets punctuation.
        if data['category'] in ['numbers','mixed'] and i%3==2:
            word=str(secrets.randbelow(999)+1)
            if data['language']=='mn-Mong':word=word.translate(str.maketrans('0123456789','᠐᠑᠒᠓᠔᠕᠖᠗᠘᠙'))
        if data['category'] in ['punctuation','mixed'] and i%2==1:word+=secrets.choice(punctuation)
        selected.append(word)
    session=TestSession.objects.create(visitor=v,browser_owned=True,user=request.user if request.user.is_authenticated else None,language=data['language'],mode=data['mode'],category=data['category'],amount=data['amount'],duration=data['amount'] if data['mode']=='time' else 0,text=' '.join(selected),demo=demo)
    response=Response({'id':str(session.id),'text':session.text,'demo':demo,'corpus':corpus,'mode':session.mode,'category':session.category,'amount':session.amount})
    response.set_signed_cookie(COOKIE,str(v),salt=COOKIE,max_age=31536000,httponly=True,secure=not settings.DEBUG,samesite='Strict')
    return response
@api_view(['POST'])
def start_test(request,pk):
    session=owned(request,pk)
    if not session:return Response({'detail':'Test not found'},status=404)
    if not isinstance(request.data.get('recover',False),bool):return Response({'detail':'Invalid recover option'},status=400)
    TestSession.objects.filter(id=session.id,started_at__isnull=True).update(started_at=timezone.now(),recovered_start=request.data.get('recover',False))
    return Response({'started':True})
class ResultInput(serializers.Serializer):
    session_id=serializers.UUIDField()
    typed_text=serializers.CharField(max_length=60000,allow_blank=True,trim_whitespace=False)
    elapsed_ms=serializers.IntegerField(min_value=100,max_value=3600000)
@api_view(['POST'])
def result(request):
    serializer=ResultInput(data=request.data);serializer.is_valid(raise_exception=True);data=serializer.validated_data
    with transaction.atomic():
        session=sessions_for(request).select_for_update().filter(id=data['session_id']).first()
        if not session:return Response({'detail':'Test not found'},status=404)
        old=Result.objects.filter(session=session).first()
        if old:return Response(result_data(old))
        if not session.started_at:return Response({'detail':'Test has not started'},status=400)
        elapsed=data['elapsed_ms']
        age=(timezone.now()-session.started_at).total_seconds()*1000
        if not session.recovered_start and elapsed>age+2000:return Response({'detail':'Invalid elapsed time'},status=400)
        full=completed(session.text,data['typed_text'])
        if session.mode=='time':
            if elapsed>session.amount*1000+500:return Response({'detail':'Invalid elapsed time'},status=400)
            if elapsed<session.amount*1000-250 and not full:return Response({'detail':'Test not finished'},status=400)
        elif not full:return Response({'detail':'Complete all words first'},status=400)
        live_age=(session.checkpoint_at-session.started_at).total_seconds() if session.checkpoint_at else 0
        eligible=(session.browser_owned and not session.demo and not session.recovered_start
                  and session.mode=='time' and session.amount==30 and session.category=='words'
                  and session.integrity_ok and session.checkpoint_seq>=8
                  and 29.5<=live_age<=32 and session.checkpoint_text==data['typed_text']
                  and all(data['typed_text'].split(' ')[:-1]))
        if eligible:elapsed=30000
        scores=score(session.text,data['typed_text'],elapsed)
        eligible=eligible and 0<scores['wpm']<=220 and scores['accuracy']>=80
        saved=Result.objects.create(session=session,typed_text=data['typed_text'],elapsed_ms=elapsed,
            rank_eligible=eligible,rank_reason='' if eligible else 'Practice only: live verification or test settings not eligible',**scores)
    return Response(result_data(saved),status=201)
def result_data(r):
    s=r.session
    return {'id':r.id,'language':s.language,'mode':s.mode,'category':s.category,'amount':s.amount,'demo':s.demo,'date':r.created_at.isoformat(),'elapsed_ms':r.elapsed_ms,'wpm':r.wpm,'accuracy':r.accuracy,'errors':r.errors,'saved':True,'rank_eligible':r.rank_eligible,'rank_reason':r.rank_reason}
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def history(request):
    sessions=history_sessions(request)
    rows=Result.objects.filter(session__in=sessions).select_related('session').order_by('-created_at')[:200]
    return Response([result_data(r) for r in rows])

def history_sessions(request):
    sessions=sessions_for(request)
    # Legacy UUID history remains readable; it can never confer ranked ownership.
    if browser_id(request) and not request.user.is_authenticated:
        try:sessions=sessions|TestSession.objects.filter(visitor=UUID(request.headers.get('X-Visitor-ID','')),browser_owned=False,user__isnull=True)
        except ValueError:pass
    return sessions
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leaderboard(request):
    # This is device ranking, without claiming verified user identity or anti-cheat.
    rows=Result.objects.filter(rank_eligible=True,session__demo=False,session__mode='time',session__amount=30,session__category='words',created_at__gte=timezone.now()-timedelta(days=30)).select_related('session','session__user')
    language=request.query_params.get('language','mn-Cyrl')
    rows=rows.filter(session__language=language).order_by('-wpm','-accuracy','created_at')
    best={}
    for row in rows:
        key='user:'+str(row.session.user_id) if row.session.user_id else 'browser:'+str(row.session.visitor)
        if key not in best:best[key]=row
        if len(best)==50:break
    return Response([{'rank':i+1,'name':r.session.user.username if r.session.user_id else 'Бичээч '+str(r.session.visitor)[:6],'speed':r.wpm,'accuracy':r.accuracy,'tests':Result.objects.filter(**({'session__user_id':r.session.user_id} if r.session.user_id else {'session__visitor':r.session.visitor,'session__user__isnull':True}),session__language=language).count()} for i,(key,r) in enumerate(best.items())])

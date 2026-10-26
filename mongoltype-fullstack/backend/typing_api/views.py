import random
import secrets
from uuid import UUID
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers
from .models import Word,TestSession,Result
from .scoring import score,completed
LANGUAGES=['en','mn-Cyrl','mn-Mong']
def visitor(request):
    try: return UUID(request.headers.get('X-Visitor-ID',''))
    except (ValueError,AttributeError): raise serializers.ValidationError({'detail':'Missing visitor identifier'})
def owned(request,pk):
    try: return TestSession.objects.get(id=pk,visitor=visitor(request))
    except (TestSession.DoesNotExist,ValueError): return None
class NewInput(serializers.Serializer):
    language=serializers.ChoiceField(choices=LANGUAGES)
    mode=serializers.ChoiceField(choices=['time','words'])
    category=serializers.ChoiceField(choices=['words','punctuation','numbers','mixed'])
    amount=serializers.IntegerField(min_value=1,max_value=200)
    demo=serializers.BooleanField(default=False)
@api_view(['POST'])
def new_test(request):
    v=visitor(request); serializer=NewInput(data=request.data);serializer.is_valid(raise_exception=True);data=serializer.validated_data
    valid=[15,30,60,120] if data['mode']=='time' else [10,25,50,100]
    if data['amount'] not in valid:return Response({'detail':'Invalid amount'},status=400)
    pool=list(Word.objects.filter(language=data['language'],verified=True).values_list('text',flat=True));demo=False
    if not pool and data['demo']:
        pool=list(Word.objects.filter(language=data['language']).values_list('text',flat=True));demo=bool(pool)
    if not pool:return Response({'detail':'Үгийн сан хоосон байна. backend хавтаст setup командыг ажиллуулна уу.'},status=503)
    count=600 if data['mode']=='time' else data['amount']; selected=[]
    punctuation=['᠂','᠃','᠄','᠁'] if data['language']=='mn-Mong' else [',','.','!','?',';']
    for i in range(count):
        word=secrets.choice(pool)
        if len(pool)>1 and selected and word==selected[-1]:word=pool[(pool.index(word)+1)%len(pool)]
        # Every third token gets a number; every second token gets punctuation.
        if data['category'] in ['numbers','mixed'] and i%3==2:word=str(secrets.randbelow(999)+1)
        if data['category'] in ['punctuation','mixed'] and i%2==1:word+=secrets.choice(punctuation)
        selected.append(word)
    session=TestSession.objects.create(visitor=v,language=data['language'],mode=data['mode'],category=data['category'],amount=data['amount'],duration=data['amount'] if data['mode']=='time' else 0,text=' '.join(selected),demo=demo)
    return Response({'id':str(session.id),'text':session.text,'demo':demo,'mode':session.mode,'category':session.category,'amount':session.amount})
@api_view(['POST'])
def start_test(request,pk):
    session=owned(request,pk)
    if not session:return Response({'detail':'Test not found'},status=404)
    TestSession.objects.filter(id=session.id,started_at__isnull=True).update(started_at=timezone.now())
    return Response({'started':True})
class ResultInput(serializers.Serializer):
    session_id=serializers.UUIDField()
    typed_text=serializers.CharField(max_length=60000,allow_blank=True,trim_whitespace=False)
    elapsed_ms=serializers.IntegerField(min_value=100,max_value=3600000)
@api_view(['POST'])
def result(request):
    v=visitor(request); serializer=ResultInput(data=request.data);serializer.is_valid(raise_exception=True);data=serializer.validated_data
    with transaction.atomic():
        session=TestSession.objects.select_for_update().filter(id=data['session_id'],visitor=v).first()
        if not session:return Response({'detail':'Test not found'},status=404)
        old=Result.objects.filter(session=session).first()
        if old:return Response(result_data(old))
        if not session.started_at:return Response({'detail':'Test has not started'},status=400)
        elapsed=data['elapsed_ms']
        age=(timezone.now()-session.started_at).total_seconds()*1000
        if elapsed>age+2000:return Response({'detail':'Invalid elapsed time'},status=400)
        full=completed(session.text,data['typed_text'])
        if session.mode=='time':
            if elapsed>session.amount*1000+500:return Response({'detail':'Invalid elapsed time'},status=400)
            if elapsed<session.amount*1000-250 and not full:return Response({'detail':'Test not finished'},status=400)
        elif not full:return Response({'detail':'Complete all words first'},status=400)
        scores=score(session.text,data['typed_text'],elapsed)
        saved=Result.objects.create(session=session,typed_text=data['typed_text'],elapsed_ms=elapsed,**scores)
    return Response(result_data(saved),status=201)
def result_data(r):
    s=r.session
    return {'id':r.id,'language':s.language,'mode':s.mode,'category':s.category,'amount':s.amount,'demo':s.demo,'date':r.created_at.isoformat(),'elapsed_ms':r.elapsed_ms,'wpm':r.wpm,'accuracy':r.accuracy,'errors':r.errors,'saved':True}
@api_view(['GET'])
def history(request):
    rows=Result.objects.filter(session__visitor=visitor(request)).select_related('session').order_by('-created_at')[:200]
    return Response([result_data(r) for r in rows])
@api_view(['GET'])
def leaderboard(request):
    # This is device ranking, without claiming verified user identity or anti-cheat.
    rows=Result.objects.filter(session__demo=False,session__mode='time',session__amount=30,session__category='words',created_at__gte=timezone.now()-timedelta(days=30)).select_related('session')
    language=request.query_params.get('language','mn-Cyrl')
    rows=rows.filter(session__language=language).order_by('-wpm','-accuracy','created_at')
    best={}
    for row in rows:
        key=str(row.session.visitor)
        if key not in best:best[key]=row
        if len(best)==50:break
    return Response([{'rank':i+1,'name':'Бичээч '+key[:6],'speed':r.wpm,'accuracy':r.accuracy,'tests':Result.objects.filter(session__visitor=r.session.visitor,session__language=language).count()} for i,(key,r) in enumerate(best.items())])

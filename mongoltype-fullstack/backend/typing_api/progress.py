from collections import Counter
from difflib import SequenceMatcher

from django.db.models import Avg, Count, Max
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Result
from .scoring import completed, units

FIELDS = ('language', 'mode', 'category', 'amount', 'demo')


class ProgressInput(serializers.Serializer):
    language = serializers.ChoiceField(choices=['en', 'mn-Cyrl', 'mn-Mong'])
    mode = serializers.ChoiceField(choices=['time', 'words'])
    category = serializers.ChoiceField(choices=['words', 'punctuation', 'numbers', 'mixed'])
    amount = serializers.IntegerField(min_value=1, max_value=200)
    demo = serializers.BooleanField()


def mistakes(target, typed, timed):
    """Analyze final text, excluding the untouched tail of a timed exercise."""
    letters, words = Counter(), Counter()
    expected, actual = target.split(' '), typed.split(' ')
    full = completed(target, typed)
    for index, word in enumerate(actual):
        if index >= len(expected):
            break
        if index == len(actual) - 1 and not word:
            continue
        wanted, entered = units(expected[index]), units(word)
        partial = timed and not full and index == len(actual) - 1 and not typed.endswith(' ')
        if partial:
            wanted = wanted[:len(entered)]
        if wanted == entered:
            continue
        words[expected[index]] += 1
        for operation, start, end, _, _ in SequenceMatcher(None, wanted, entered, autojunk=False).get_opcodes():
            if operation in ('replace', 'delete'):
                letters.update(wanted[start:end])
    return letters, words


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def progress(request):
    from .views import history_sessions, result_data
    rows = Result.objects.filter(session__in=history_sessions(request))
    fields = ['session__' + field for field in FIELDS]
    grouped = rows.values(*fields).annotate(count=Count('id'), best_wpm=Max('wpm')).order_by(*fields)
    groups = [{**{field: row['session__' + field] for field in FIELDS},
               'count': row['count'], 'best_wpm': row['best_wpm']} for row in grouped]
    if not groups:
        return Response({'groups': [], 'selected': None, 'summary': None, 'recent': [], 'history': [],
                         'letters': [], 'words': [], 'comparison': None})
    if request.query_params:
        serializer = ProgressInput(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        selected = serializer.validated_data
    else:
        latest = rows.select_related('session').order_by('-created_at', '-id').first()
        selected = {field: getattr(latest.session, field) for field in FIELDS}
    rows = rows.filter(**{'session__' + field: value for field, value in selected.items()})
    stats = rows.aggregate(count=Count('id'), average_wpm=Avg('wpm'), average_accuracy=Avg('accuracy'))
    best = rows.select_related('session').order_by('-wpm', '-accuracy', 'created_at', 'id').first()
    recent = list(rows.select_related('session').order_by('-created_at', '-id')[:50])
    letters, words = Counter(), Counter()
    for row in rows.select_related('session').iterator(chunk_size=100):
        bad_letters, bad_words = mistakes(row.session.text, row.typed_text, row.session.mode == 'time')
        letters.update(bad_letters)
        words.update(bad_words)
    comparison = None
    if len(recent) >= 10:
        current = sum(row.wpm for row in recent[:5]) / 5
        previous = sum(row.wpm for row in recent[5:10]) / 5
        comparison = {'current': round(current, 1), 'previous': round(previous, 1),
                      'delta': round(current - previous, 1)}
    return Response({
        'groups': groups, 'selected': selected,
        'summary': {**stats, 'average_wpm': round(stats['average_wpm'], 1) if stats['count'] else None,
                    'average_accuracy': round(stats['average_accuracy'], 1) if stats['count'] else None,
                    'best': result_data(best) if best else None,
                    'latest_delta': round(recent[0].wpm - recent[1].wpm, 1) if len(recent) > 1 else None},
        'recent': [result_data(row) for row in reversed(recent[:10])],
        'history': [result_data(row) for row in recent], 'comparison': comparison,
        'letters': [{'text': text, 'count': count} for text, count in letters.most_common(10)],
        'words': [{'text': text, 'count': count} for text, count in words.most_common(10)],
    })

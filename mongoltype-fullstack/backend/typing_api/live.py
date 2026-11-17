from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Result
from .scoring import units


class CheckpointInput(serializers.Serializer):
    seq = serializers.IntegerField(min_value=1, max_value=10000)
    typed_text = serializers.CharField(max_length=60000, allow_blank=True, trim_whitespace=False)


@api_view(['POST'])
def checkpoint(request, pk):
    from .views import sessions_for
    serializer = CheckpointInput(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    with transaction.atomic():
        session = sessions_for(request).select_for_update().filter(id=pk).first()
        if not session:
            return Response({'detail': 'Test not found'}, status=404)
        if not session.started_at:
            return Response({'detail': 'Test has not started'}, status=400)
        if Result.objects.filter(session=session).exists():
            return Response({'detail': 'Test already finished'}, status=409)
        if data['seq'] == session.checkpoint_seq and data['typed_text'] == session.checkpoint_text:
            return Response({'accepted': True})
        if data['seq'] <= session.checkpoint_seq:
            return Response({'detail': 'Stale checkpoint'}, status=409)
        now = timezone.now()
        gap = (now - (session.checkpoint_at or session.started_at)).total_seconds()
        age = (now - session.started_at).total_seconds()
        previous, current = units(session.checkpoint_text), units(data['typed_text'])
        prefix = 0
        while prefix < min(len(previous), len(current)) and previous[prefix] == current[prefix]:
            prefix += 1
        edits = max(len(previous) - prefix, len(current) - prefix)
        # Server receipt times, bounded changes and a continuous sequence.
        session.integrity_ok &= (data['seq'] == session.checkpoint_seq + 1 and gap <= 4
                                 and edits <= max(8, gap * 35)
                                 and (session.mode != 'time' or age <= session.amount + 2))
        session.checkpoint_seq = data['seq']
        session.checkpoint_text = data['typed_text']
        session.checkpoint_at = now
        session.save(update_fields=['integrity_ok', 'checkpoint_seq', 'checkpoint_text', 'checkpoint_at'])
    return Response({'accepted': True})

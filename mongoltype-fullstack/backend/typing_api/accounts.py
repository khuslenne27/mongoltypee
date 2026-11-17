import json
from uuid import uuid4

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.cache import never_cache
from rest_framework.throttling import SimpleRateThrottle

from .models import TestSession


class AccountThrottle(SimpleRateThrottle):
    scope = 'account'
    rate = '10/min'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


def user_data(user):
    return {'id': user.pk, 'username': user.username} if user.is_authenticated else None


def claim_browser(request, user):
    from .views import browser_id
    visitor = browser_id(request)
    if visitor:
        TestSession.objects.filter(visitor=visitor, browser_owned=True, user__isnull=True).update(user=user)


def input_data(request):
    throttle = AccountThrottle()
    if not throttle.allow_request(request, None):
        return None, JsonResponse({'detail': 'Олон удаа оролдлоо. Түр хүлээгээд дахин оролдоно уу.'}, status=429)
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict) or not all(isinstance(data.get(k), str) for k in ('username', 'password')):
            raise ValueError()
        if len(data['password']) > 256:
            raise ValueError()
        data['username'] = get_user_model().normalize_username(data['username'].strip()).casefold()
        return data, None
    except (ValueError, UnicodeDecodeError):
        return None, JsonResponse({'detail': 'Нэвтрэх нэр, нууц үгээ зөв оруулна уу.'}, status=400)


@require_GET
@never_cache
@ensure_csrf_cookie
def me(request):
    return JsonResponse({'user': user_data(request.user), 'csrf_token': get_token(request)})


@require_POST
@never_cache
@csrf_protect
def register(request):
    if request.user.is_authenticated:
        return JsonResponse({'detail': 'Бүртгэлтэй хэрэглэгчээсээ эхлээд гарна уу.'}, status=409)
    data, error = input_data(request)
    if error is not None:
        return error
    user = get_user_model()(username=data['username'])
    if get_user_model().objects.filter(username__iexact=user.username).exists():
        return JsonResponse({'detail': 'Энэ нэвтрэх нэр бүртгэлтэй байна.'}, status=409)
    try:
        user.full_clean(exclude=['password'])
        validate_password(data['password'], user=user)
    except ValidationError as error:
        return JsonResponse({'detail': 'Бүртгэлийн мэдээллээ шалгана уу.', 'errors': error.messages}, status=400)
    try:
        with transaction.atomic():
            user.set_password(data['password'])
            user.save()
            claim_browser(request, user)
    except IntegrityError:
        return JsonResponse({'detail': 'Энэ нэвтрэх нэр бүртгэлтэй байна.'}, status=409)
    login(request, user)
    return JsonResponse({'user': user_data(user), 'csrf_token': get_token(request)}, status=201)


@require_POST
@never_cache
@csrf_protect
def sign_in(request):
    if request.user.is_authenticated:
        return JsonResponse({'detail': 'Өөр бүртгэлд нэвтрэхийн өмнө гарна уу.'}, status=409)
    data, error = input_data(request)
    if error is not None:
        return error
    existing = get_user_model().objects.filter(username__iexact=data['username']).first()
    user = authenticate(request, username=existing.username if existing else data['username'], password=data['password'])
    if user is None:
        return JsonResponse({'detail': 'Нэвтрэх нэр эсвэл нууц үг буруу байна.'}, status=400)
    with transaction.atomic():
        claim_browser(request, user)
    login(request, user)
    return JsonResponse({'user': user_data(user), 'csrf_token': get_token(request)})


@require_POST
@never_cache
@csrf_protect
def sign_out(request):
    from django.conf import settings
    from .views import COOKIE
    logout(request)
    response = JsonResponse({'user': None, 'csrf_token': get_token(request)})
    response.set_signed_cookie(COOKIE, str(uuid4()), salt=COOKIE, max_age=31536000,
                               httponly=True, secure=not settings.DEBUG, samesite='Strict')
    return response

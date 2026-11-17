from django.contrib import admin
from django.urls import path
from typing_api import views
from typing_api.live import checkpoint
from typing_api.progress import progress
from typing_api import accounts
urlpatterns=[path('admin/',admin.site.urls),path('api/tests',views.new_test),path('api/tests/<uuid:pk>/start',views.start_test),path('api/results',views.result),path('api/history',views.history),path('api/leaderboard',views.leaderboard)]
urlpatterns += [path('api/tests/<uuid:pk>/checkpoint',checkpoint)]
urlpatterns += [path('api/identity',views.identity)]
urlpatterns += [path('api/progress',progress)]
urlpatterns += [path('api/auth/me',accounts.me),path('api/auth/register',accounts.register),
                path('api/auth/login',accounts.sign_in),path('api/auth/logout',accounts.sign_out)]

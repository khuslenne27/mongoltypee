from django.contrib import admin
from django.urls import path
from typing_api import views
urlpatterns=[path('admin/',admin.site.urls),path('api/tests',views.new_test),path('api/tests/<uuid:pk>/start',views.start_test),path('api/results',views.result),path('api/history',views.history),path('api/leaderboard',views.leaderboard)]

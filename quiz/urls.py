from django.urls import path
from .views import quiz_list


urlpatterns = [
    path('', quiz_list, name='quiz_list'),
]
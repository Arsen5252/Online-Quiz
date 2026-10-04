from django.urls import path
from .views import all_quizzes, create_quiz, quiz_list, my_quizzes, quiz_detail


urlpatterns = [
    path('', quiz_list, name='quiz_list'),
    path('create/', create_quiz, name='create_quiz'),
    path('my-quizzes/', my_quizzes, name='my_quizzes'),
    path('quizzes/', all_quizzes, name='all_quizzes'),
    path('quiz/<int:quiz_id>/', quiz_detail, name='quiz_detail'),
]
from django.urls import path
from .views import quiz_list, create_quiz, my_quizzes, all_quizzes, quiz_detail, edit_quiz, delete_quiz

urlpatterns = [
    path('', quiz_list, name='quiz_list'),
    path('create/', create_quiz, name='create_quiz'),
    path('my-quizzes/', my_quizzes, name='my_quizzes'),
    path('quizzes/', all_quizzes, name='all_quizzes'),
    path('quiz/<int:quiz_id>/', quiz_detail, name='quiz_detail'),
    path('quiz/<int:quiz_id>/edit/', edit_quiz, name='edit_quiz'),
    path('quiz/<int:quiz_id>/delete/', delete_quiz, name='delete_quiz'),
]
from django.shortcuts import render
from .models import Quiz


def quiz_list(request):
    quizzes = Quiz.objects.all()

    return render(request, 'quiz_list.html', {
        'quizzes': quizzes
    })
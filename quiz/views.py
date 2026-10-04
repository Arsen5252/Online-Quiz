import json
import secrets
import string

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .models import Quiz, Question, Answer
from .forms import QuizForm


def quiz_list(request):
    quizzes = Quiz.objects.all()

    return render(request, 'quiz_list.html', {
        'quizzes': quizzes
    })

@login_required(login_url='login')
def my_quizzes(request):
    quizzes = (
        Quiz.objects
        .filter(author=request.user)
        .order_by('-created_at')
    )

    return render(request, 'my_quizzes.html', {
        'quizzes': quizzes
    })


def generate_invitation_code():
    alphabet = string.ascii_uppercase + string.digits

    while True:
        code = ''.join(secrets.choice(alphabet) for _ in range(8))

        if not Quiz.objects.filter(invitation_code=code).exists():
            return code


@login_required(login_url='login')
def create_quiz(request):

    if request.method == 'POST':

        form = QuizForm(request.POST)

        try:
            questions = json.loads(
                request.POST.get('questions', '[]')
            )
        except json.JSONDecodeError:
            questions = []

        error = None

        # Перевіряємо питання
        if not questions:
            error = 'Додай хоча б одне запитання.'

        elif len(questions) > 50:
            error = 'Максимум 50 запитань.'

        else:
            for number, question in enumerate(questions, start=1):

                answers = question.get('answers', [])

                if not question.get('text', '').strip():
                    error = f'Заповни текст запитання №{number}.'
                    break

                if len(answers) != 4:
                    error = f'У запитанні №{number} повинно бути 4 відповіді.'
                    break

                if any(not answer.strip() for answer in answers):
                    error = f'Заповни всі відповіді в запитанні №{number}.'
                    break

                if question.get('correct') not in range(4):
                    error = f'Обери правильну відповідь у запитанні №{number}.'
                    break

                if question.get('type') not in ('text', 'image', 'video'):
                    error = f'Невідомий тип запитання №{number}.'
                    break

                if (
                    question['type'] == 'image'
                    and not request.FILES.get(f'image_{number - 1}')
                ):
                    error = f'Додай зображення до запитання №{number}.'
                    break

                if (
                    question['type'] == 'video'
                    and not question.get('video', '').strip()
                ):
                    error = f'Додай посилання на відео в запитанні №{number}.'
                    break

                try:
                    time_limit = int(question.get('time_limit', 30))
                    score = int(question.get('score', 1))

                    if not 5 <= time_limit <= 300:
                        raise ValueError

                    if not 1 <= score <= 100:
                        raise ValueError

                except (ValueError, TypeError):
                    error = f'Перевір таймер і бали в запитанні №{number}.'
                    break

        # Якщо все правильно — створюємо вікторину
        if form.is_valid() and not error:

            with transaction.atomic():

                quiz = form.save(commit=False)

                quiz.author = request.user
                quiz.invitation_code = generate_invitation_code()

                quiz.save()

                # Створюємо питання
                for index, data in enumerate(questions):

                    question = Question.objects.create(
                        quiz=quiz,
                        text=data['text'].strip(),
                        question_type=data['type'],
                        time_limit=int(data['time_limit']),
                        score=int(data['score']),
                        order=index,
                        video=(
                            data.get('video', '').strip()
                            if data['type'] == 'video'
                            else ''
                        )
                    )

                    # Зображення
                    if data['type'] == 'image':

                        question.image = request.FILES.get(
                            f'image_{index}'
                        )

                        question.save(
                            update_fields=['image']
                        )

                    # Відповіді
                    for answer_index, answer_text in enumerate(
                        data['answers']
                    ):

                        Answer.objects.create(
                            question=question,
                            text=answer_text.strip(),
                            is_correct=(
                                answer_index == data['correct']
                            )
                        )

            return redirect('quiz_list')

    else:
        form = QuizForm()
        error = None

    return render(request, 'create_quiz.html', {
        'form': form,
        'error': error
    })

@login_required(login_url='login')
def quiz_detail(request, quiz_id):
    quiz = Quiz.objects.get(
        id=quiz_id,
        author=request.user
    )

    return render(request, 'quiz_detail.html', {
        'quiz': quiz
    })

def all_quizzes(request):
    quizzes = Quiz.objects.all().order_by('-created_at')

    return render(request, 'quiz_list.html', {
        'quizzes': quizzes
    })
import json
import secrets
import string

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.views.decorators.http import require_POST

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

@login_required(login_url='login')
def edit_quiz(request, quiz_id):
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        author=request.user
    )

    questions_queryset = (
        quiz.questions
        .prefetch_related('answers')
        .order_by('order', 'id')
    )

    existing_questions = [
        {
            'id': question.id,
            'text': question.text,
            'type': question.question_type,
            'time_limit': question.time_limit,
            'score': question.score,
            'video': question.video or '',
            'image_url': (
                question.image.url if question.image else ''
            ),
            'answers': [
                answer.text
                for answer in question.answers.all()
            ],
            'correct': next(
                (
                    index
                    for index, answer in enumerate(
                        question.answers.all()
                    )
                    if answer.is_correct
                ),
                0
            )
        }
        for question in questions_queryset
    ]

    error = None

    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)

        try:
            questions_data = json.loads(
                request.POST.get('questions', '[]')
            )
        except json.JSONDecodeError:
            questions_data = None

        if not isinstance(questions_data, list):
            error = 'Неправильний формат запитань.'

        elif not 1 <= len(questions_data) <= 50:
            error = 'Кількість запитань повинна бути від 1 до 50.'

        else:
            existing_ids = {
                question.id: question
                for question in questions_queryset
            }

            used_ids = set()
            url_validator = URLValidator()

            for index, data in enumerate(questions_data):
                number = index + 1

                if not isinstance(data, dict):
                    error = f'Некоректне запитання №{number}.'
                    break

                question_id = data.get('id')

                if question_id is not None:
                    if (
                        type(question_id) is not int
                        or question_id not in existing_ids
                        or question_id in used_ids
                    ):
                        error = f'Некоректний ID запитання №{number}.'
                        break

                    used_ids.add(question_id)

                question_type = data.get('type')
                question_text = data.get('text')
                answers = data.get('answers')
                correct = data.get('correct')
                video = data.get('video', '')

                if (
                    not isinstance(question_text, str)
                    or not question_text.strip()
                ):
                    error = f'Заповни запитання №{number}.'
                    break

                if question_type not in ('text', 'image', 'video'):
                    error = f'Невідомий тип запитання №{number}.'
                    break

                if (
                    not isinstance(answers, list)
                    or len(answers) != 4
                    or any(
                        not isinstance(answer, str)
                        or not answer.strip()
                        or len(answer) > 300
                        for answer in answers
                    )
                ):
                    error = f'Перевір 4 відповіді в запитанні №{number}.'
                    break

                if type(correct) is not int or correct not in range(4):
                    error = f'Обери правильну відповідь №{number}.'
                    break

                try:
                    time_limit = int(data.get('time_limit'))
                    score = int(data.get('score'))

                    if not 5 <= time_limit <= 300:
                        raise ValueError

                    if not 1 <= score <= 100:
                        raise ValueError

                except (ValueError, TypeError):
                    error = f'Перевір таймер і бали №{number}.'
                    break

                if question_type == 'video':
                    if not isinstance(video, str) or not video.strip():
                        error = f'Додай посилання на відео №{number}.'
                        break

                    try:
                        url_validator(video.strip())
                    except ValidationError:
                        error = f'Некоректне посилання №{number}.'
                        break

                image = request.FILES.get(f'image_{index}')

                if question_type == 'image':
                    old_image = (
                        existing_ids[question_id].image
                        if question_id is not None
                        else None
                    )

                    if not image and not old_image:
                        error = f'Додай зображення №{number}.'
                        break

                    if image:
                        if (
                            image.size > 5 * 1024 * 1024
                            or image.content_type not in (
                                'image/jpeg',
                                'image/png',
                                'image/webp'
                            )
                        ):
                            error = f'Неприпустиме зображення №{number}.'
                            break

        if form.is_valid() and not error:
            with transaction.atomic():
                quiz = form.save()

                retained_ids = set()

                for index, data in enumerate(questions_data):
                    question_id = data.get('id')

                    if question_id is not None:
                        question = existing_ids[question_id]
                    else:
                        question = Question(quiz=quiz)

                    question.text = data['text'].strip()
                    question.question_type = data['type']
                    question.time_limit = int(data['time_limit'])
                    question.score = int(data['score'])
                    question.order = index

                    question.video = (
                        data.get('video', '').strip()
                        if data['type'] == 'video'
                        else ''
                    )

                    if data['type'] == 'image':
                        uploaded = request.FILES.get(
                            f'image_{index}'
                        )
                        if uploaded:
                            question.image = uploaded
                    else:
                        question.image = None

                    question.save()
                    retained_ids.add(question.id)

                    question.answers.all().delete()

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

                quiz.questions.exclude(
                    id__in=retained_ids
                ).delete()

            return redirect('quiz_detail', quiz_id=quiz.id)

    else:
        form = QuizForm(instance=quiz)

    return render(request, 'edit_quiz.html', {
        'quiz': quiz,
        'form': form,
        'error': error,
        'existing_questions': existing_questions,
    })


@login_required(login_url='login')
@require_POST
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        author=request.user
    )

    quiz.delete()

    return redirect('my_quizzes')
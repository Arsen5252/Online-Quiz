from django.db import models
from django.contrib.auth.models import User


class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    invitation_code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPES = [
        ('text', 'Текст'),
        ('image', 'Зображення'),
        ('video', 'Відео'),
    ]

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    text = models.TextField()
    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPES,
        default='text'
    )
    image = models.ImageField(
        upload_to='questions/images/',
        blank=True,
        null=True
    )
    video = models.URLField(
        blank=True,
        null=True
    )
    time_limit = models.PositiveIntegerField(
        default=30
    )

    score = models.PositiveIntegerField(
        default=1
    )

    order = models.PositiveIntegerField(
        default=0
    )

    def __str__(self):
        return self.text[:50]


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text[:50]

class QuizResult(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='results'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quiz_results',
        null=True,
        blank=True
    )
    nickname = models.CharField(max_length=50)
    score = models.PositiveIntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nickname} - {self.quiz.title} - {self.score}"

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}"

class QuestionResult(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='question_results'
    )
    quiz_result = models.ForeignKey(
        QuizResult,
        on_delete=models.CASCADE,
        related_name='question_results'
    )
    selected_answer = models.ForeignKey(
        Answer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.quiz_result.user.username} - {self.question.text[:50]} - {'Correct' if self.is_correct else 'Incorrect'}"


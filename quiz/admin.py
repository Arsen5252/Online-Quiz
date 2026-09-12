from django.contrib import admin

# Register your models here.
from .models import Quiz, Question, Answer, QuizResult, QuestionResult

admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(QuizResult)
admin.site.register(QuestionResult)

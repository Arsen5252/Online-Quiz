from django import forms
from .models import Quiz


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description']

        labels = {
            'title': 'Назва вікторини',
            'description': 'Опис',
        }

        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Наприклад: Вікторина про Minecraft',
                'class': 'quiz-input',
            }),

            'description': forms.Textarea(attrs={
                'placeholder': 'Коротко розкажи про свою вікторину...',
                'class': 'quiz-input',
                'rows': 4,
            }),
        }
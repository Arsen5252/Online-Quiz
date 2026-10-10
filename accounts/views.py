from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django import forms
from django.contrib.auth.models import User

from .forms import RegisterForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('quiz_list')

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('quiz_list')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {
        'form': form
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('quiz_list')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            login(request, form.get_user())
            return redirect('quiz_list')
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {
        'form': form
    })


@require_POST
def logout_view(request):
    logout(request)
    return redirect('quiz_list')


@login_required(login_url='login')
def profile_view(request):
    return render(request, 'accounts/profile.html')

class ProfileSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

        labels = {
            'username': 'Нікнейм',
            'first_name': "Ім'я",
            'last_name': 'Прізвище',
            'email': 'Email',
        }

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'settings-input',
                'placeholder': 'Твій нікнейм'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'settings-input',
                'placeholder': "Ім'я"
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'settings-input',
                'placeholder': 'Прізвище'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'settings-input',
                'placeholder': 'example@gmail.com'
            }),
        }


@login_required(login_url='login')
def profile_settings(request):
    profile_form = ProfileSettingsForm(instance=request.user)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'profile':
            profile_form = ProfileSettingsForm(
                request.POST,
                instance=request.user
            )

            if profile_form.is_valid():
                profile_form.save()
                messages.success(
                    request,
                    'Дані профілю успішно оновлено!'
                )
                return redirect('profile_settings')

        elif action == 'password':
            password_form = PasswordChangeForm(
                user=request.user,
                data=request.POST
            )

            if password_form.is_valid():
                user = password_form.save()

                update_session_auth_hash(request, user)

                messages.success(
                    request,
                    'Пароль успішно змінено!'
                )
                return redirect('profile_settings')

    return render(request, 'accounts/settings.html', {
        'profile_form': profile_form,
        'password_form': password_form,
    })
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

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
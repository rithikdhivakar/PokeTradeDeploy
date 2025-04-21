from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages


def index(request):
    return render(request, 'home/index.html', {'template_data': {'title': 'Home'}})

def about(request):
    return render(request, 'home/about.html', {'template_data': {'title': 'About'}})


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home.index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'home/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home.index')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'home/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home.index')

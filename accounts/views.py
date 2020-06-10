from django.shortcuts import render
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import logout as django_logout
from django.contrib.auth import authenticate, login
from .forms import SignupForm, LoginForm
from .models import Profile

# Create your views here.
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            return redirect('accounts:login')
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {
        'form' : form,
    })


def login_check(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        name = request.POST.get('username')
        pwd = request.POST.get('password')

        user = authenticate(username=name, password=pwd)

        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'accounts/login.html')
    else:
        form = LoginForm()
        return render(request, 'accounts/login.html', {
            'form': form,
        })
    
def logout(request):
    django_logout(request)
    return redirect('/')


def user_profile(request, user):
    user = get_object_or_404(Profile, pk=user)
    
    return render(request, 'accounts/profile.html', {
        'user': user,
    })
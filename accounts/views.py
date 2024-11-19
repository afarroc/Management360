# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

from .forms import UserLoginForm, UserRegistrationForm

# Create your views here.

def indexView(request):
    return render(request,'index.html')

@login_required()
def dashboardView(request):
    return render(request,'dashboard.html')

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

# accounts/views.py
from django.shortcuts import render, redirect
from .forms import UserLoginForm
from django.contrib.auth import authenticate, login

from django.shortcuts import render, redirect
from .forms import UserLoginForm
from django.contrib.auth import authenticate, login

def login_view(request):
  if request.method == 'POST':
    form = UserLoginForm(request.POST)
    if form.is_valid():  
      username = form.cleaned_data['username']
      password = form.cleaned_data['password']
      user = authenticate(username=username, password=password) or authenticate(email=username, password=password)
      if user is not None:
        login(request, user)
        if 'remember' in form.cleaned_data and form.cleaned_data['remember']:
          request.session.set_expiry(604800) 
        return redirect('home')
  else:
    form = UserLoginForm()
  return render(request, 'login.html', {'form': form, 'title': 'Login'})
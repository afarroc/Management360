from django.urls import reverse_lazy
from django.contrib.auth import logout, login as auth_login
from .forms import SignUpForm  # Importa el formulario personalizado
from django.shortcuts import render, redirect

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)  # Utiliza el formulario personalizado
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('index')
    else:
        form = SignUpForm()  # Utiliza el formulario personalizado
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect(reverse_lazy('login'))

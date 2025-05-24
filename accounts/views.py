# Standard library imports
import logging
import os

# Django imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import (
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.contrib.auth.models import User
from django.contrib.auth.views import (
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.core.mail import send_mail as original_send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

# Local imports
from .forms import SignUpForm
from tools.views.file_views import file_tree_view

# Logger configuration
logger = logging.getLogger(__name__)


def anonymous_required(function=None, redirect_url=None):
    """
    Decorator for views that checks that the user is NOT logged in, redirecting
    to the specified page if necessary.
    """
    if not redirect_url:
        redirect_url = "index"

    actual_decorator = user_passes_test(lambda u: u.is_anonymous, login_url=redirect_url)

    if function:
        return actual_decorator(function)
    return actual_decorator


@login_required
def accounts_view(request):
    """Dashboard view for authenticated users."""
    if request.user.is_staff:
        context = {
            "title": "Admin Dashboard",
            "user": request.user,
        }
    else:
        context = {
            "title": "User Dashboard",
            "user": request.user,
        }
    return render(request, "accounts/accounts_dashboard.html", context)


def signup_view(request):
    """View for user registration."""
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Registration successful! You are now logged in.")
            return redirect("index")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


@anonymous_required(redirect_url="index")
def login_view(request):
    """View for user login."""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        logger.info(f"Attempting login for user: {username}")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            logger.info(f"Login successful for user: {username}")
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get("next", "index")
            return redirect(next_url)
        else:
            logger.warning(f"Login failed for user: {username}")
            messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")


def logout_view(request):
    """View for user logout."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect(reverse_lazy("login"))


class CustomPasswordChangeView(PasswordChangeView):
    """Custom view for password change."""

    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("password_change_done")
    form_class = PasswordChangeForm

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed successfully!")
        return super().form_valid(form)


class CustomPasswordResetView(PasswordResetView):
    """Custom view for password reset."""

    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")
    form_class = PasswordResetForm

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        if not User.objects.filter(email=email).exists():
            messages.error(
                self.request, "This email address doesn't have an associated account."
            )
            return self.form_invalid(form)
        messages.info(
            self.request, "We've emailed you instructions for setting your password."
        )
        return super().form_valid(form)

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """Override send_mail to log emails in debug mode."""
        if settings.DEBUG:
            logger.info("Simulating email sending:")
            logger.info(f"Subject: {subject_template_name}")
            logger.info(f"To: {to_email}")
            logger.info(f"Context: {context}")
        else:
            super().send_mail(
                subject_template_name,
                email_template_name,
                context,
                from_email,
                to_email,
                html_email_template_name,
            )

    def reset_to_default_password(self, request, username):
        """Allows an admin to reset a user's password to a generic default password."""
        if not request.user.is_staff:
            messages.error(request, "You do not have permission to perform this action.")
            return redirect("password_reset")

        try:
            user = User.objects.get(username=username)
            default_password = "DefaultPassword123"
            user.set_password(default_password)
            user.save()
            messages.success(
                request, f"The password for {username} has been reset to the default password."
            )
        except User.DoesNotExist:
            messages.error(request, f"User with username {username} does not exist.")

        return redirect("password_reset")


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom view for password reset confirmation."""

    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")
    form_class = SetPasswordForm

    def form_valid(self, form):
        messages.success(self.request, "Your password has been reset successfully!")
        return super().form_valid(form)
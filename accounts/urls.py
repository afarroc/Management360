from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    accounts_view,
    signup_view,
    login_view,
    logout_view,
    CustomPasswordChangeView,
    CustomPasswordResetView,
    CustomPasswordResetConfirmView
)

urlpatterns = [
    # Accounts dashboard
    path('', accounts_view, name='accounts'),
    
    # Basic authentication
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Password change (for logged in users)
    path('password-change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='accounts/password_change_done.html'
         ), 
         name='password_change_done'),
    
    # Password reset
    path('password-reset/', 
         CustomPasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt'
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         CustomPasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]
from django.urls import path
from . import views
from django.contrib.auth.views import LoginView,LogoutView
urlpatterns = [
    path('',views.indexView,name="account"),
    path('dashboard/',views.dashboardView,name="account_dashboard"),
    path('login/',views.login_view, name="login"),
    path('register/',views.register_view, name="register"),
    path('logout/',LogoutView.as_view(next_page='dashboard'),name="logout"),
]
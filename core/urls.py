from django.urls import path
from . import views
from events.setup_views import SetupView

urlpatterns = [
    path('', views.home_view, name='home'),
    path('', views.home_view, name='index'),    
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('setup/', SetupView.as_view(), name='setup'),
    path('<int:days>/', views.home_view, name="index"),
    path('<int:days>/<int:days_ago>/', views.home_view, name="index"),
    path('about/', views.about, name="about"),
    path('faq/', views.faq, name="faq"),
    path('contact/', views.contact, name="contact"),
    path('blank/', views.blank, name="blank"),
    ]



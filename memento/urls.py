from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import memento, MementoConfigCreateView, MementoConfigUpdateView

urlpatterns = [
    # Main views
    path('', memento, name='memento_default'),  # Default view with form
    path('try/', memento, name='memento_try'),  # Temporary trial view
    
    # Configuration management
    path('config/create/', MementoConfigCreateView.as_view(), name='memento_create'),
    path('config/update/<int:pk>/', MementoConfigUpdateView.as_view(), name='memento_update'),
    
    # Visualization views
    path('view/<str:frequency>/<str:birth_date>/<str:death_date>/', memento, name='memento'),
    
    # Authentication
    path('logout/', LogoutView.as_view(), name='logout'),
]
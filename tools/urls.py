from django.urls import path
from . import views
from .views import file_tree_view

urlpatterns = [
    path('calculate_agents/', views.calculate_agents, name='calculate_agents'),
    # File tree view
    path("file-tree/", file_tree_view, name="file_tree"),
]
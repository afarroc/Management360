from django.urls import path
from . import views

urlpatterns = [
    path('calculate_agents/', views.calculate_agents, name='calculate_agents'),
    path("file-tree/", views.file_tree_view, name="file_tree"),
    path('upload-data/', views.upload_data, name='upload_data'),
    
]
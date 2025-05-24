from django.urls import path, include
from tools.views.other_tools import calculate_agents
from tools.views.file_views import file_tree_view

urlpatterns = [
    path('calculate_agents/', calculate_agents, name='calculate_agents'),
    path("file-tree/", file_tree_view, name="file_tree"),
    path('upload-data/', include('tools.urls.data_upload')),  # Referencia al otro archivo
]
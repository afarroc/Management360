from django.urls import path, include

urlpatterns = [
    path('data/', include('tools.urls.data_upload')),
    path('tools/', include('tools.urls.tools')),
    path('upload-data/', include('tools.urls.data_upload')),  # Add this line
]
from django.urls import path, include

urlpatterns = [
    path('tools/', include('tools.urls.tools_urls')),
    path('data/', include('tools.urls.data_upload')),
]
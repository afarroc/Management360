from django.urls import path
from tools.views.data_upload import upload_csv

urlpatterns = [
    path('upload/', upload_csv, name='data_upload'),
]
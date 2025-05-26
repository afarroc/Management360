from django.urls import path
from tools.views.data_upload import upload_csv, clipboard_details, export_clipboard_csv

urlpatterns = [
    path('upload/', upload_csv, name='data_upload'),
    path('clipboard-details/', clipboard_details, name='clipboard_details'),
    path('export-clipboard-csv/', export_clipboard_csv, name='export_clipboard_csv'),
]
from django.urls import path
from .views import (
    CurriculumDetailView, CurriculumUpdateView, PublicCurriculumView,
    DocumentUploadView, ImageUploadView, DatabaseUploadView,
    FileDeleteView, DocumentListView
)

app_name = 'cv'

urlpatterns = [
    path('', CurriculumDetailView.as_view(), name='cv_detail'),
    path('editar/', CurriculumUpdateView.as_view(), name='cv_edit'),
    path('ver/<int:user_id>/', PublicCurriculumView.as_view(), name='view_cv'),
    
    # Document management
    path('documentos/', DocumentListView.as_view(), name='docsview'),
    path('documentos/subir/documento/', DocumentUploadView.as_view(), name='document_upload'),
    path('documentos/subir/imagen/', ImageUploadView.as_view(), name='image_upload'),
    path('documentos/subir/base-datos/', DatabaseUploadView.as_view(), name='upload_db'),
    path('documentos/eliminar/<str:file_type>/<int:file_id>/', FileDeleteView.as_view(), name='delete_file'),
]
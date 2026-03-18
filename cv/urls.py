# cv/urls.py - Añadir las nuevas URLs

from django.urls import path
from .views import (
    CurriculumDetailView, CurriculumCreateView, CurriculumUpdateView, 
    PublicCurriculumView, DocumentUploadView, ImageUploadView, 
    DatabaseUploadView, FileDeleteView, DocumentListView,
    EditPersonalInfoView, EditExperienceView, EditEducationView, EditSkillsView, TraditionalProfileView
)

app_name = 'cv'

urlpatterns = [
    # CV principal
    path('', CurriculumDetailView.as_view(), name='cv_detail'),
    path('crear/', CurriculumCreateView.as_view(), name='cv_create'),
    path('editar/', CurriculumUpdateView.as_view(), name='cv_edit'),
    path('ver/<int:user_id>/', PublicCurriculumView.as_view(), name='view_cv'),
    
    # Edición por secciones
    path('editar/personal/', EditPersonalInfoView.as_view(), name='edit_personal'),
    path('editar/experiencia/', EditExperienceView.as_view(), name='edit_experience'),
    path('editar/educacion/', EditEducationView.as_view(), name='edit_education'),
    path('editar/habilidades/', EditSkillsView.as_view(), name='edit_skills'),
    
    # Document management
    path('documentos/', DocumentListView.as_view(), name='docsview'),
    path('documentos/subir/documento/', DocumentUploadView.as_view(), name='document_upload'),
    path('documentos/subir/imagen/', ImageUploadView.as_view(), name='image_upload'),
    path('documentos/subir/base-datos/', DatabaseUploadView.as_view(), name='upload_db'),
    path('documentos/eliminar/<str:file_type>/<int:file_id>/', FileDeleteView.as_view(), name='delete_file'),
    path('view/<int:user_id>/tradicional/', TraditionalProfileView.as_view(), name='traditional_profile'),
]
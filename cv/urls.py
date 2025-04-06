# cv/urls.py
from django.urls import path
from .views import cv_detail, cv_edit, CurriculumView, ViewCurriculumView, delete_profile_picture
from . import views

urlpatterns = [
    # Vista principal del CV
    path('', cv_detail, name='cv_detail'),
    
    # Edición básica
    path('editar/', cv_edit, name='cv_edit'),
    
    # Edición completa con formsets
    path('editar-completo/', CurriculumView.as_view(), name='full_cv_edit'),
    
    # Vista pública
    path('ver/<int:user_id>/', ViewCurriculumView.as_view(), name='view_cv'),
    
    # Eliminación de imagen
    path('eliminar-imagen/', delete_profile_picture, name='delete_profile_picture'),
    
    
    
        # Document viewer
    path('documents/delete/<str:file_type>/<int:file_id>/', views.delete_file, name='delete_file'),
    path('documents/docsview/', views.document_view, name='docsview'),
    path('documents/doc_upload/', views.DocumentUploadView.as_view(), name='document_upload'),
    path('documents/img_upload/', views.ImageUploadView.as_view(), name='image_upload'),
    path('documents/upload/database/', views.UploadDatabase.as_view(), name='upload_db'),
    path('documents/upload/xlsx/', views.upload_xlsx, name='upload_xlsx'),
        # Url para subir pandas
    path('about/upload/', views.upload_image, name='upload_image'),
    
]
# cv/urls.py
from django.urls import path
from .views import (
    cv_detail,
    cv_edit,
    CurriculumView,
    ViewCurriculumView,
    delete_profile_picture
)

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
]
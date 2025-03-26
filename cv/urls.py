# cv/urls.py
from django.urls import path
from .views import (
    cv_detail,
    cv_edit,
    CurriculumView,
    ViewCurriculumView
)

urlpatterns = [
    # Vistas básicas
    path('', cv_detail, name='cv_detail'),
    path('edit/', cv_edit, name='cv_edit'),
    
    # Vistas completas con formsets
    path('full-edit/', CurriculumView.as_view(), name='full_cv_edit'),
    path('view/<int:user_id>/', ViewCurriculumView.as_view(), name='view_cv'),
]
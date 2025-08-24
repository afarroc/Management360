from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('category/<slug:category_slug>/', views.course_list, name='course_list_by_category'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('<int:course_id>/enroll/', views.enroll, name='enroll'),
    path('<slug:slug>/', views.course_detail, name='course_detail'),
    # CORRECCIÓN: Asegúrate de que estas URLs estén definidas correctamente
    path('<slug:slug>/learn/', views.course_learning, name='course_learning'),
    path('<slug:slug>/learn/<int:lesson_id>/', views.course_learning, name='course_learning_lesson'),
    path('lesson/<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
    path('<int:course_id>/review/', views.add_review, name='add_review'),
    
    # URLs para tutores
    path('manage/', views.manage_courses, name='manage_courses'),
    path('manage/create/', views.create_course, name='create_course'),
    path('manage/<slug:slug>/edit/', views.edit_course, name='edit_course'),
    path('manage/<slug:slug>/analytics/', views.course_analytics, name='course_analytics'),
]
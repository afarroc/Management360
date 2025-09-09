from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.index, name='index'),  # Página principal con contenido general
    path('category/<slug:category_slug>/', views.course_list, name='course_list_by_category'),
    path('dashboard/', views.dashboard, name='dashboard'),  # Dashboard para usuarios autenticados
    path('courses/', views.course_list, name='courses_list'),  # Lista de cursos disponibles
    path('<int:course_id>/enroll/', views.enroll, name='enroll'),
    # URLs para tutores (deben ir antes de <slug:slug>/)
    path('manage/', views.manage_courses, name='manage_courses'),
    path('manage/create/', views.create_course, name='create_course'),
    path('manage/create/wizard/', views.create_course_wizard, name='create_course_wizard'),
    path('manage/<slug:slug>/edit/', views.edit_course, name='edit_course'),
    path('manage/<slug:slug>/analytics/', views.course_analytics, name='course_analytics'),

    # URLs para gestión de contenido
    path('manage/<slug:slug>/content/', views.manage_content, name='manage_content'),
    path('manage/<slug:slug>/modules/create/', views.create_module, name='create_module'),
    path('manage/<slug:slug>/modules/<int:module_id>/edit/', views.edit_module, name='edit_module'),
    path('manage/<slug:slug>/modules/<int:module_id>/delete/', views.delete_module, name='delete_module'),
    path('manage/<slug:slug>/modules/<int:module_id>/duplicate/', views.duplicate_module, name='duplicate_module'),
    path('manage/<slug:slug>/modules/<int:module_id>/statistics/', views.module_statistics, name='module_statistics'),
    path('manage/<slug:slug>/modules/<int:module_id>/progress/', views.module_progress, name='module_progress'),
    path('manage/<slug:slug>/modules/bulk-actions/', views.bulk_module_actions, name='bulk_module_actions'),
    path('manage/<slug:slug>/modules/reorder/', views.reorder_modules, name='reorder_modules'),
    path('modules/overview/', views.modules_overview, name='modules_overview'),
    path('manage/<slug:slug>/modules/<int:module_id>/lessons/create/', views.create_lesson, name='create_lesson'),
    path('manage/<slug:slug>/modules/<int:module_id>/lessons/<int:lesson_id>/edit/', views.edit_lesson, name='edit_lesson'),
    path('manage/<slug:slug>/modules/<int:module_id>/lessons/<int:lesson_id>/delete/', views.delete_lesson, name='delete_lesson'),

    # URLs para gestión de categorías
    path('manage/categories/', views.manage_categories, name='manage_categories'),
    path('manage/categories/create/', views.create_category, name='create_category'),
    path('manage/categories/quick-create/', views.quick_create_category, name='quick_create_category'),
    path('manage/categories/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('manage/categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),

    # URLs de administración
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin/users/<int:user_id>/edit/', views.edit_user, name='edit_user'),

    path('<slug:slug>/', views.course_detail, name='course_detail'),
    path('<slug:slug>/learn/', views.course_learning, name='course_learning'),
    path('<slug:slug>/learn/<int:lesson_id>/', views.course_learning, name='course_learning_lesson'),
    path('lesson/<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
    path('<int:course_id>/review/', views.add_review, name='add_review'),
]
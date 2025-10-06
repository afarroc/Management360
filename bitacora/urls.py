from django.urls import path
from . import views

app_name = 'bitacora'

urlpatterns = [
    path('', views.BitacoraListView.as_view(), name='dashboard'),  # Dashboard principal
    path('list/', views.BitacoraListView.as_view(template_name='bitacora/entry_list.html'), name='list'),  # Lista simple
    path('<int:pk>/', views.BitacoraDetailView.as_view(), name='detail'),
    path('create/', views.BitacoraCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.BitacoraUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.BitacoraDeleteView.as_view(), name='delete'),

    # Integración con contenido estructurado de courses
    path('content-blocks/', views.content_blocks_list, name='content_blocks'),
    path('<int:entry_id>/insert-block/<int:block_id>/', views.insert_content_block, name='insert_content_block'),

    # Subida de imágenes para TinyMCE
    path('upload-image/', views.upload_image, name='upload_image'),
]
from django.urls import path
from . import views, htmx_views

app_name = 'board'

urlpatterns = [
    # Vistas normales
    path('', views.BoardListView.as_view(), name='list'),
    path('create/', views.BoardCreateView.as_view(), name='create'),
    path('<int:pk>/', views.BoardDetailView.as_view(), name='detail'),
    
    # 🔥 HTMX Endpoints - CRUD sin recarga
    path('htmx/<int:board_id>/grid/', htmx_views.board_grid, name='grid'),
    path('htmx/<int:board_id>/create-card/', htmx_views.create_card_htmx, name='create_card_htmx'),
    path('htmx/card/<int:card_id>/delete/', htmx_views.delete_card_htmx, name='delete_card_htmx'),
    path('htmx/card/<int:card_id>/toggle-pin/', htmx_views.toggle_pin_card, name='toggle_pin'),
    path('htmx/<int:board_id>/load-more/', htmx_views.load_more_cards, name='load_more'),
]
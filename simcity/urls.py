from django.urls import path
from . import views

app_name = 'simcity'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/games/', views.list_games, name='list_games'),
    path('api/games/new/', views.new_game, name='new_game'),
    path('api/game/<int:game_id>/map/', views.game_map, name='game_map'),
    path('api/game/<int:game_id>/tick/', views.tick, name='tick'),
    path('api/game/<int:game_id>/build/', views.build, name='build'),
    path('api/game/<int:game_id>/reset/', views.reset, name='reset'),
    path('api/game/<int:game_id>/generate_block/', views.generate_block, name='generate_block'),
    path('api/game/<int:game_id>/census/', views.census, name='census'),
    path('api/game/<int:game_id>/tasks/', views.task_status, name='task_status'),
    path('api/game/<int:game_id>/delete/', views.delete_game, name='delete_game'),
    path('api/game/<int:game_id>/add_money/', views.add_money, name='add_money'),
]
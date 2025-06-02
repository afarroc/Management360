# app/urls.py  
from django.urls import path  
from . import views  

urlpatterns = [  
    path('', views.kpi_home, name='kpi_home'),
    # Dashboard de AHT  
    path('dashboard/', views.aht_dashboard, name='dashboard'),  
    # Exportar datos para Power BI/Tableau  
    path('export-data/', views.export_data, name='export_data'),      
    path('generate-data/', views.generate_fake_data, name='generate_data'),
]
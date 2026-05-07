from django.urls import path
from . import views 

urlpatterns = [
    path('', views.home, name='home'),
    path('historique/', views.historique, name='historique'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('api/data/', views.receive_data, name='receive_data'),
]
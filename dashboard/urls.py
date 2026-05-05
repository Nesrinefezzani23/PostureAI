from django.urls import path
from . import views 

urlpatterns = [
    path('', views.home, name='home'),
    path('api/data/', views.receive_data, name='receive_data'),
]
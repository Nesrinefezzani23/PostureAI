from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')), # On dit à Django d'aller voir dans dashboard/urls.py
]
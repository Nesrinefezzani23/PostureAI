from django.urls import path
from . import views 

from django.urls import path
from . import views 
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.home, name='home'),
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.signout, name='logout'),
    path('register-api/', views.RegisterView.as_view(), name='register_api'),
    path('login-api/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login-api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('historique/', views.historique, name='historique'),
    path('profil/', views.profile_settings, name='profile_settings'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('api/data/', views.receive_data, name='receive_data'),
    path('api/alertes/', views.get_alertes, name='get_alertes'),
]
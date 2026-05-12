from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'InicioSeccion'

urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='InicioSeccion/inisec.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]


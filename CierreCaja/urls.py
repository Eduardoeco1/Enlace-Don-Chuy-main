from django.urls import path
from . import views

app_name = 'CierreCaja'

urlpatterns = [
    path('', views.cierre_caja_view, name='cierre'),
]




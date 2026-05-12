from django.urls import path
from . import views

app_name = 'PanelControl'

urlpatterns = [
    path('', views.panel_view, name='panel'),
]

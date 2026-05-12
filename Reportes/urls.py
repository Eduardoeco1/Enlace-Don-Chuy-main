from django.urls import path
from . import views

app_name = 'Reportes'

urlpatterns = [
    path('',               views.reportes_view,        name='reporte'),
    path('exportar-pdf/',  views.exportar_reporte_pdf,  name='exportar_pdf'),
    path('exportar-csv/',  views.exportar_reporte_csv,  name='exportar_csv'),
]


from django.urls import path
from . import views

app_name = 'Reportes'

urlpatterns = [
    path(
        '',
        views.reporte_view,
        name='reporte'
    ),

    path(
        'exportar-pdf/',
        views.exportar_reporte_pdf,
        name='exportar_pdf'
    ),

    path(
        'exportar-csv/',
        views.exportar_reporte_csv,
        name='exportar_csv'
    ),

    path(
        'exportar-consolidado/',
        views.exportar_consolidado_csv,
        name='exportar_consolidado'
    ),

    path(
        'exportar-sucursal/',
        views.exportar_sucursal_csv,
        name='exportar_sucursal'
    ),

    path(
        'actualizar-meta/',
        views.actualizar_meta_semanal,
        name='actualizar_meta'
    ),

    path(
        'registrar-conteo/',
        views.registrar_conteo_inventario,
        name='registrar_conteo'
    ),

    path(
        'resolver-discrepancia/<int:insumo_id>/',
        views.resolver_discrepancia,
        name='resolver_discrepancia'
    ),
]

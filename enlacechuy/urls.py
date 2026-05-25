from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from importlib import import_module

inicio_views = import_module('InicioSeccion.views')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', inicio_views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('panel-control/', include('PanelControl.urls')),
    path('reportes/', include('Reportes.urls')),
    path('entrada-mercancia/', include('EntradaMercancia.urls')),
    path('Cierre-Caja/', include('CierreCaja.urls')),
    path('inventario/', include('Inventario.urls')),
    path('perfil/', include('Perfil.urls')),
    path('personal/', include('Personal.urls')),
    path('ventas/', include('Ventas.urls')),
    path('', include('Sucursales.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



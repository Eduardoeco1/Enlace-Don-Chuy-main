from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Sucursal, Usuario

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'clave', 'ubicacion', 'activa')
    list_editable = ('activa',)

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display  = ('username', 'get_full_name', 'rol', 'sucursal', 'is_active')
    list_filter   = ('rol', 'sucursal', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    fieldsets = UserAdmin.fieldsets + (
        ('Enlace Don Chuy', {
            'fields': ('rol', 'sucursal'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Enlace Don Chuy', {
            'fields': ('rol', 'sucursal'),
        }),
    )




    
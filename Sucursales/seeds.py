"""
python manage.py shell < Sucursales/seeds.py
"""
from Sucursales.models import Sucursal, Usuario

print("🌱 Creando sucursales y usuarios base...")

# Sucursales
centro, _ = Sucursal.objects.get_or_create(
    clave='CTR',
    defaults={'nombre': 'Sucursal Centro', 'ubicacion': 'Av. Principal 100, Centro'}
)
norte, _ = Sucursal.objects.get_or_create(
    clave='NTE',
    defaults={'nombre': 'Sucursal Norte', 'ubicacion': 'Blvd. Norte 250, Polanco'}
)
sur, _ = Sucursal.objects.get_or_create(
    clave='SUR',
    defaults={'nombre': 'Sucursal Sur', 'ubicacion': 'Calle Sur 88, Pedregal'}
)

# Usuarios de prueba
usuarios = [
    {'username': 'duena',    'password': 'Duena2024!',   'rol': 'duena',    'sucursal': None,   'first_name': 'Carmen',   'last_name': 'López'},
    {'username': 'gerente1', 'password': 'Gerente2024!', 'rol': 'gerente',  'sucursal': centro, 'first_name': 'Julián',   'last_name': 'Soto'},
    {'username': 'gerente2', 'password': 'Gerente2024!', 'rol': 'gerente',  'sucursal': norte,  'first_name': 'Sofía',    'last_name': 'García'},
    {'username': 'empleado1','password': 'Emp2024!',     'rol': 'empleado', 'sucursal': centro, 'first_name': 'Mateo',    'last_name': 'Rodríguez'},
    {'username': 'empleado2','password': 'Emp2024!',     'rol': 'empleado', 'sucursal': norte,  'first_name': 'Lucía',    'last_name': 'Fernández'},
]

for u in usuarios:
    if not Usuario.objects.filter(username=u['username']).exists():
        nuevo = Usuario.objects.create_user(
            username   = u['username'],
            password   = u['password'],
            rol        = u['rol'],
            sucursal   = u['sucursal'],
            first_name = u['first_name'],
            last_name  = u['last_name'],
        )
        if u['rol'] == 'duena':
            nuevo.is_staff     = True
            nuevo.is_superuser = True
            nuevo.save()
        print(f"  ✅ {nuevo.get_full_name()} ({nuevo.get_rol_display()})")
    else:
        print(f"  ⏭️  {u['username']} ya existe")

print("✅ Seeds de Sucursales completados.")



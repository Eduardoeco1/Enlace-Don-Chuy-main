"""
Ejecutar con: python manage.py shell < Ventas/seeds.py
"""
from Ventas.models import Categoria, Producto

print("🌱 Sembrando datos iniciales de Ventas...")

# Categorías
parrilla, _    = Categoria.objects.get_or_create(nombre='Parrilla',     defaults={'icono': 'local_fire_department', 'orden': 1})
guarnic, _     = Categoria.objects.get_or_create(nombre='Guarniciones', defaults={'icono': 'restaurant',            'orden': 2})
bebidas, _     = Categoria.objects.get_or_create(nombre='Bebidas',      defaults={'icono': 'local_bar',             'orden': 3})
postres, _     = Categoria.objects.get_or_create(nombre='Postres',      defaults={'icono': 'cake',                  'orden': 4})

# Productos
productos = [
    {
        'categoria': parrilla,
        'nombre': 'Pollo a la Brasa',
        'descripcion': 'Receta tradicional al carbón',
        'precio': 95.00,
        'imagen_url': 'https://lh3.googleusercontent.com/aida-public/AB6AXuAQFjoMZSrumr5r25CVxHgvqxiLgwfMN-x41PzcXJMZB_zxVM51MsAIj3cpyErU1B_JuhPJD4onXSd9JH1pvCa53j65r9tumTO1OOfmlK1v-dysV7sLttnf3i7ViilzgTePS3-G0SXC2EqFlJuN2_CkUWdUqQO91u_Fv0YExSqennL1bGztSF7cHTvsWBvQe_wx1KfcPcNPNUbe2JtVWUXkfE4vne4ZhEjkLdeBwluFoHZr54sB42hPMJCAepA6iqYzFFU1xMi-j3Tz',
    },
    {
        'categoria': parrilla,
        'nombre': 'Costillas BBQ',
        'descripcion': '6 horas de ahumado',
        'precio': 145.00,
        'imagen_url': 'https://lh3.googleusercontent.com/aida-public/AB6AXuDng2m8KEIQD73t9rdHfX5eAY8SUP-0lAQiRcRxj4RtCUBOcPfAEair5f1avZtICe9Wsx-YTm6v04Wmd4P0sEpJrUlNXeKBGXaLrN_CZzgtvG3AQiT89I62O7XbDf6Mm0dDA5UGbiqpmDyvHoEZ_NkhRgY_Ef9kH2OsgHSHj7PuxtMxvhzb3gth8zvPRHiVZzVUSeLsLB074pMKXsWCOJoSGHo3o1H2CnXXM1GtVK-a8UFqvIDvaGdA7VXw-MtUAIToQHCrOkDLKNQa',
    },
    {
        'categoria': parrilla,
        'nombre': 'Burger Carbón',
        'descripcion': '200g de Angus a la parrilla',
        'precio': 95.00,
        'imagen_url': 'https://lh3.googleusercontent.com/aida-public/AB6AXuA_F_2jnYFj9-a1LNPxfCN5gSgItCFhp4IFgIJkkpd--rVcV-mRBxfINFSpqGhSgtq2HFU2OmEvNVVgt8q4DW0TOhLahzwwwq1NoN1zU05bduuvPeayWMIM0dKp7ZpfcUHhWrCdvvRHMQRFIXy-crzgrC13pfJhdJ-pmihMQD7nLvwHdgSlkMkmJtMXHfzCqZTtInhvgHPZUVpt4XO5B8WFz0eASFlkHMQzyGTG_C7DDSRRSjU24MR05TkfxMR1AvOnGBaTodui1W5U',
    },
    {
        'categoria': guarnic,
        'nombre': 'Papas Nativas',
        'descripcion': 'Andinas con sal de maras',
        'precio': 45.00,
        'imagen_url': 'https://lh3.googleusercontent.com/aida-public/AB6AXuD7uTZTanowuIJ7MM9m8HQV0Yq8Meg9d5k1IcaL8549UBIpTP9BolYX9oQQAkiuR0MIfv-ZyV_7j0jfHAbfv3V4GXllfdf8xNBOdQUtg2LuTZ9ZtybZs1zZsFdJZ9DHTDK_f7qTFCYMq7r8Be0zVy9W-Dv9ZyAkh0CuXsueG_KjT_UrzeS1Rv7qMYEpbEXmZb3iC_84vJSEGDcgVg-ODKP8LUoQRBK2j7f07WzZ6jZGN5eowbGlvFHcjEnWaEG0C275ThHNDSwPOcib',
    },
    {
        'categoria': bebidas,
        'nombre': 'Chicha Morada',
        'descripcion': 'Vaso personal de la casa',
        'precio': 35.00,
        'imagen_url': 'https://lh3.googleusercontent.com/aida-public/AB6AXuBzfi452JhBnT1b8ZVLCI1TteO9Hz1o5pw6LFqcH1OneqhhCCaZp1wkP5yFSUVdHOFz-Q9YbCrpS7VsPgmN8eZ7koYEiaetloaRuRqi13pHwT-BbXtLSJdCXIM1LktcR3q3DemoG8WYBvA9Nt1rfvYM9PcZ4BMN1E5ekpEiCdrMl9fjkgZYIcUPHOtFdb1Z51F70uGEbG95lkDkfhviCbL5c3aVZaa8GtvhHO9wIwzbm4Uo-GrFjcIGX1E2zhtKX-sp060Dv3G7AsuQ',
    },
    {
        'categoria': postres,
        'nombre': 'Picarones',
        'descripcion': 'Miel de chancaca artesanal',
        'precio': 55.00,
        'imagen_url': 'https://lh3.googleusercontent.com/aida-public/AB6AXuALN3bnzUMAzrbPeuK4DPxuXH33YXCbjP8R_eNlTQL8OjnVdxoyvyD5au45vtG9E-Mf_1d4ZhgyTV9cjvmvWanTQfiC7ZiqHKrOCapJDGEe-RMmtT70f9Gh1ylYulD4eCwh9OxWlPlN96_PY0MC58-vrJtf5TlZT1Fg0dLROU-W_72YQLTcSGMjz_pVv6UqoLWg9luoG_Lr-dSDk99WXz8dLcoqcTKnxATH3vIfaChBqvdx-ajWlLefOucJr4w-SSLD_4wrZfPTlr4a',
    },
]

for p in productos:
    obj, created = Producto.objects.get_or_create(
        nombre=p['nombre'],
        defaults=p
    )
    estado = '✅ creado' if created else '⏭️  ya existe'
    print(f"  {estado}: {obj.nombre}")

print("✅ Seeds completados.")


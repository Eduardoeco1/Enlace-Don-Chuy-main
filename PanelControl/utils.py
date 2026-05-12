from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta

def generar_sugerencia(Producto, Venta):
    ahora = timezone.now()

    # --- Alerta de stock bajo ---
    productos_bajos = Producto.objects.filter(stock__lt=5).order_by('stock')
    if productos_bajos.exists():
        p = productos_bajos.first()
        return f'⚠️ Alerta: "{p.nombre}" está por agotarse ({p.stock} unidades restantes).'

    # --- Ventas lentas ---
    hace_3h = ahora - timedelta(hours=3)
    ventas_recientes = Venta.objects.filter(creado_en__gte=hace_3h).count()
    if ventas_recientes == 0:
        return '🔔 El movimiento está lento. Considera lanzar una promoción del turno.'

    # --- Comparación semanal ---
    inicio_semana     = ahora - timedelta(days=7)
    inicio_semana_ant = ahora - timedelta(days=14)

    ventas_esta_semana = Venta.objects.filter(
        creado_en__gte=inicio_semana
    ).aggregate(total=Sum('total'))['total'] or 0

    ventas_semana_ant = Venta.objects.filter(
        creado_en__gte=inicio_semana_ant,
        creado_en__lt=inicio_semana
    ).aggregate(total=Sum('total'))['total'] or 0

    if ventas_semana_ant > 0:
        variacion = ((ventas_esta_semana - ventas_semana_ant) / ventas_semana_ant) * 100
        if variacion > 0:
            return f'📈 ¡Buen trabajo! Las ventas subieron un {variacion:.1f}% vs la semana pasada.'
        else:
            return f'📉 Las ventas bajaron un {abs(variacion):.1f}% vs la semana pasada. Revisa la estrategia.'

    return '💡 El pico de ventas suele ser a las 20:00. Considera reforzar el personal en ese horario.'


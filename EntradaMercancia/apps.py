from django.apps import AppConfig


class EntradamercanciaConfig(AppConfig):
    name = 'EntradaMercancia'
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        """Importar signals al iniciar la aplicación"""
        import EntradaMercancia.signals

        
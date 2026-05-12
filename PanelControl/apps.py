from django.apps import AppConfig

class PanelcontrolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'PanelControl'

    def ready(self):
        # Al importar aquí, Django registra los "triggers" 
        # que descuentan el stock automáticamente.
        import PanelControl.signals

        
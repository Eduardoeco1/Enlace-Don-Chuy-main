from django.apps import AppConfig


class PersonalConfig(AppConfig):
    name = 'Personal'
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        """Importar signals al iniciar la aplicación"""
        import Personal.signals

        
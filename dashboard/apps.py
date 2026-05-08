from django.apps import AppConfig

class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):
        import os
        # Evite le double démarrage en mode dev (runserver lance 2 processus)
        if os.environ.get('RUN_MAIN') == 'true':
            from dashboard.mqtt_client import start_mqtt_thread
            start_mqtt_thread()
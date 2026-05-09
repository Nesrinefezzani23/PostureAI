from django.apps import AppConfig
import os

class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):
        # RUN_MAIN évite le double démarrage avec runserver
        # Avec daphne ce check n'est pas nécessaire mais ne fait pas de mal
        if os.environ.get('RUN_MAIN') != 'false':
            from dashboard.mqtt_client import start_mqtt_thread
            start_mqtt_thread()
from django.apps import AppConfig
# async
from .tasks import start_scheduler

class GazeboConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gazebo'

    def ready(self):
        start_scheduler()

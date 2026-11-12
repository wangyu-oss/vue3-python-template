from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import sys
        if any(arg in sys.argv for arg in ('migrate', 'makemigrations', 'seed_demo.py', 'collectstatic')):
            return
        from core.jobs import start
        start()

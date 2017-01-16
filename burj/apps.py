from django.apps import AppConfig


class BurjConfig(AppConfig):
    name = 'burj'

    def ready(self):
        import burj.signals  # noqa

from django.apps import AppConfig  # pragma: no cover


class FictionOutlinesConfig(AppConfig):  # pragma: no cover
    name = 'fiction_outlines'
    verbose_name = 'Fiction Outlines'

    def ready(self):  # pragma: no cover
        from . import receivers  # noqa: F401

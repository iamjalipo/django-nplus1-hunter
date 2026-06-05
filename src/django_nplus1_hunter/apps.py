import sys
import warnings

from django.apps import AppConfig
from django.conf import settings


class NPlus1HunterConfig(AppConfig):
    name = "django_nplus1_hunter"
    verbose_name = "N+1 Hunter"

    def ready(self):
        """
        Safety check: Ensure the app is not accidentally deployed to production.
        """
        if not getattr(settings, "DEBUG", False):
            # Try to determine if we are running in a test suite.
            # If so, we might not want to scream, but in real production we do.
            is_testing = "test" in sys.argv or "pytest" in sys.modules

            if not is_testing:
                warnings.warn(
                    "\n\n"
                    "========================================================================\n"
                    "WARNING: django-nplus1-hunter is installed but settings.DEBUG is False.\n"
                    "This tool incurs significant performance overhead by capturing stack\n"
                    "traces for every database query. It MUST NOT be used in production.\n"
                    "Please remove 'django_nplus1_hunter' from INSTALLED_APPS.\n"
                    "========================================================================\n",
                    RuntimeWarning,
                )

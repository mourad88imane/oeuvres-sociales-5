import os

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


def pytest_configure():
    from django.conf import settings

    settings.DEBUG = False
    # Remove debug toolbar to avoid rendering errors in test responses
    settings.INSTALLED_APPS = [app for app in settings.INSTALLED_APPS if app != "debug_toolbar"]
    settings.MIDDLEWARE = [
        m for m in settings.MIDDLEWARE if m != "debug_toolbar.middleware.DebugToolbarMiddleware"
    ]

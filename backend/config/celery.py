"""
============================================================
CELERY — Configuration du worker de tâches asynchrones
============================================================
"""
import os
from celery import Celery
from celery.signals import setup_logging

# Settings Django par défaut pour Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("oeuvres_sociales")

# Lecture de la config depuis Django settings (namespace CELERY_)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Découverte automatique des tâches dans tous les apps/*/tasks.py
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tâche de test pour vérifier que Celery fonctionne."""
    print(f"Request: {self.request!r}")

# ============================================================
# DOCKERFILE BACKEND — Django + Gunicorn
# Multi-stage build : dev et prod dans le même fichier
# ============================================================

# ── Stage 1 : Base commune ────────────────────────────────
FROM python:3.12-slim AS base

LABEL maintainer="equipe-dev@oeuvres-sociales.dz"
LABEL description="Plateforme Oeuvres Sociales — Backend Django"

# Variables d'environnement Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root (sécurité)
RUN groupadd --gid 1001 django && \
    useradd --uid 1001 --gid django --shell /bin/bash --create-home django

WORKDIR /app

# ── Stage 2 : Développement ──────────────────────────────
FROM base AS development

# Installer toutes les dépendances de dev
COPY requirements/development.txt requirements/development.txt
COPY requirements/base.txt requirements/base.txt
RUN pip install -r requirements/development.txt

# Copier le code source
COPY --chown=django:django . .

# Créer les dossiers nécessaires
RUN mkdir -p logs staticfiles media && \
    chown -R django:django logs staticfiles media

USER django

EXPOSE 8000

# Utiliser runserver Django en dev (avec auto-reload)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ── Stage 3 : Production ─────────────────────────────────
FROM base AS production

# Installer uniquement les dépendances de prod
COPY requirements/production.txt requirements/production.txt
COPY requirements/base.txt requirements/base.txt
RUN pip install -r requirements/production.txt

# Copier le code source
COPY --chown=django:django . .

# Créer les dossiers nécessaires
RUN mkdir -p logs staticfiles media && \
    chown -R django:django logs staticfiles media

USER django

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/auth/verify/ || exit 1

# Gunicorn en production
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--worker-connections", "1000", \
     "--timeout", "60", \
     "--keepalive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "config.wsgi:application"]

# Version qui marche garantie - Pas de multi-stage complexe
FROM python:3.11-slim

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python (celles qui échouent avec requirements.txt)
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pydantic==2.5.0 \
    requests==2.31.0 \
    python-multipart==0.0.6 \
    psutil==5.9.6

# Copier l'application
COPY app.py /app.py

# Variables d'environnement
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Démarrage simple
CMD ["python", "/app.py"]
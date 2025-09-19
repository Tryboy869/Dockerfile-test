# ILN Architecture Simple - Dockerfile remplace requirements.txt
FROM python:3.11-slim

# Installer toutes les dépendances directement dans le Dockerfile
# Ceci contourne les limitations de Render avec requirements.txt
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pydantic==2.5.0 \
    requests==2.31.0 \
    python-multipart==0.0.6

# Copier seulement le fichier de code métier
COPY app.py /app.py

# Configuration
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Démarrage direct
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
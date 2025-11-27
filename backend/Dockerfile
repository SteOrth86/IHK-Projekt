FROM python:3.12-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# Logs direkt durchreichen, kein Buffering
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Restlichen Code ins Image kopieren
COPY . .

# Standard-Port für FastAPI/Uvicorn
EXPOSE 8000

# Startbefehl für das Backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

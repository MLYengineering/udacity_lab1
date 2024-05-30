# Verwende ein offizielles Python Runtime als Basisimage
FROM python:3.9-slim

# Setze Arbeitsverzeichnis
WORKDIR /app

# Kopiere die Anforderungen und installiere Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den Rest des Anwendungscodes
COPY . .

# Stelle das Startskript bereit
CMD ["./startup.sh"]

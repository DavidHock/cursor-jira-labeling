#!/bin/bash

# Erstelle die .env-Datei
cat <<EOL > .env
SECRET_KEY=my-super-secret-key
JIRA_INSTANCE=infosim.atlassian.net
EOL

echo ".env-Datei erstellt."

# Erstelle das Dockerfile
cat <<EOL > Dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /shared
ENV PYTHONUNBUFFERED=1
CMD ["python", "jira_app.py"]
EOL

echo "Dockerfile erstellt."

# Erstelle docker-compose.yml
cat <<EOL > docker-compose.yml
version: '3.8'
services:
  jira_app:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./shared_volume:/shared
    environment:
      - SECRET_KEY=\${SECRET_KEY}
      - JIRA_INSTANCE=\${JIRA_INSTANCE}
    networks:
      - jira_network
networks:
  jira_network:
    driver: bridge
EOL

echo "docker-compose.yml erstellt."

# Erstelle requirements.txt
cat <<EOL > requirements.txt
flask
requests
python-dotenv
EOL

echo "requirements.txt erstellt."

# Erstelle den shared_volume-Ordner, falls nicht vorhanden
mkdir -p shared_volume
echo "Shared Volume-Verzeichnis erstellt."

chmod +x setup.sh
echo "Setup-Skript fertig! Führe './setup.sh' aus, um das Setup zu starten."

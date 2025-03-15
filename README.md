# Jira Flask App

Diese Anwendung ist eine Flask-basierte Web-App zur Verwaltung und Analyse von Jira-Issues. Sie läuft in einem Docker-Container und nutzt ein gemeinsames Dateisystem (`/shared`), um Logs und Sitzungsdaten zu speichern.

## 📖 Projektbeschreibung
Die Jira Flask App ermöglicht es Benutzern, Jira-Issues effizient zu suchen und zu verwalten. Sie bietet eine benutzerfreundliche Oberfläche und nutzt moderne Technologien, um die Interaktion mit Jira zu optimieren.

## 📦 Installation
1. **Repository klonen**
   ```bash
   git clone git@localhost:hock/jiraapp.git
   cd jiraapp
   ```

2. **Erforderliche Dateien erstellen**
   Falls nicht bereits vorhanden, führe das Setup-Skript aus:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **.env-Datei anpassen**
   Bearbeite die `.env`-Datei und setze die richtigen Werte:
   ```
   SECRET_KEY=my-super-secret-key
   JIRA_INSTANCE=infosim.atlassian.net
   ```

## 🐳 Docker-Nutzung
### **Projekt mit Docker starten**
```bash
docker-compose up --build
```

### **Container stoppen**
```bash
docker-compose down
```

### **Logs einsehen**
```bash
docker logs -f jira_app
```

## 🚀 Nutzung
Nach dem Starten der Anwendung kannst du die Web-App in deinem Browser unter `http://localhost:5000` erreichen. Nutze die bereitgestellten Funktionen, um Jira-Issues zu suchen und zu verwalten.

## 📦 Deployment
Um die Anwendung in einer Produktionsumgebung bereitzustellen, stelle sicher, dass alle Umgebungsvariablen korrekt konfiguriert sind und führe die Docker-Befehle wie oben beschrieben aus.

## 🔧 Entwicklung
Falls du lokal entwickeln möchtest, kannst du die App ohne Docker ausführen:
```bash
pip install -r requirements.txt
python jira_app.py
```

## 📜 Lizenz
Dieses Projekt steht unter der MIT-Lizenz.

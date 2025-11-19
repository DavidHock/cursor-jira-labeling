# Jira Flask Application

A Flask-based web application for managing and analyzing Jira issues. The application provides a user-friendly interface for searching, viewing, and updating Jira issues with research project assignments and chargeable status.

## 📋 Features

- **Authentication**: Secure login with Jira email and API token
- **Issue Search**: Search for issues using Jira filter IDs
- **Issue Hierarchy**: View issue details with linked issues
- **Worklog Analysis**: Display worklog statistics and pie charts
- **Issue Updates**: Update research project and chargeable status
- **Session Management**: Persistent session storage

## 🏗️ Project Structure

```
jira/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration settings
│   ├── routes/              # Route blueprints
│   │   ├── auth.py          # Authentication routes
│   │   ├── issues.py        # Issue viewing routes
│   │   ├── search.py        # Search routes
│   │   └── update.py        # Update routes
│   ├── services/            # Business logic layer
│   │   ├── jira_service.py  # Jira API interactions
│   │   └── session_service.py  # Session management
│   └── utils/               # Utility functions
├── templates/               # Jinja2 templates
├── shared_volume/           # Shared data directory (Docker)
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
├── run.py                  # Application entry point
└── .env.example            # Environment variables template
```

## 📦 Installation

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (for containerized deployment)
- Jira account with API token

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd jira
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

   The application will be available at `https://localhost:8081` (with SSL) or `http://localhost:8081`.

### Docker Deployment

1. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Open your browser and navigate to `http://localhost:8081`

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
SECRET_KEY=your-secret-key-here
JIRA_INSTANCE=infosim.atlassian.net
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=8081
```

### Jira API Token

1. Go to your Jira account settings
2. Navigate to Security → API tokens
3. Create a new API token
4. Use your email and API token to log in to the application

## 🚀 Usage

1. **Login**: Enter your Jira email and API token
2. **Search**: Enter a Jira filter ID to search for issues
3. **View Issue**: Review issue details, hierarchy, and worklog statistics
4. **Update Issue**: Set research project and chargeable status
5. **Navigate**: Move through issues using the navigation buttons

## 🐳 Docker Commands

```bash
# Build and start containers
docker-compose up --build

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down

# Rebuild after code changes
docker-compose up --build --force-recreate
```

## 🧪 Development

### Code Structure

The application follows Flask best practices:

- **Application Factory Pattern**: Used in `app/__init__.py`
- **Blueprint Organization**: Routes are organized by feature
- **Service Layer**: Business logic separated from routes
- **Configuration Management**: Centralized in `app/config.py`

### Adding New Features

1. Create route blueprints in `app/routes/`
2. Add business logic to `app/services/`
3. Register blueprints in `app/__init__.py`
4. Update templates in `templates/`

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues and questions, please open an issue in the repository.

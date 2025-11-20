# Jira Labeling Tool

A modern full-stack application for managing and analyzing Jira issues. Features a **Flask REST API backend** and an **Angular 17 frontend** for a state-of-the-art user experience.

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
├── app/                     # Flask Backend (REST API)
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration settings
│   ├── routes/              # API route blueprints
│   │   ├── auth.py          # Authentication API
│   │   ├── issues.py        # Issue viewing API
│   │   ├── search.py        # Search API
│   │   └── update.py        # Update API
│   ├── services/            # Business logic layer
│   │   ├── jira_service.py  # Jira API interactions
│   │   └── session_service.py  # Session management
│   └── utils/               # Utility functions
├── frontend/                # Angular 17 Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/  # Angular components
│   │   │   ├── services/    # API services
│   │   │   ├── models/      # TypeScript models
│   │   │   └── guards/      # Route guards
│   │   └── styles.scss      # Global styles
│   ├── Dockerfile          # Frontend Docker image
│   └── nginx.conf          # Nginx configuration
├── shared_volume/           # Shared data directory (Docker)
├── Dockerfile              # Backend Docker image
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
├── run.py                  # Application entry point
└── .env.example            # Environment variables template
```

## 📦 Installation

### Prerequisites

- Python 3.9+ (for backend)
- Node.js 20+ and npm (for frontend development)
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

5. **Run the backend API**
   ```bash
   python run.py
   ```
   The API will be available at `http://localhost:8082`

6. **Run the frontend** (in a separate terminal)
   ```bash
   cd frontend
   npm install
   npm start
   ```
   The frontend will be available at `http://localhost:4200`

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
   - Frontend: `http://localhost:4200`
   - Backend API: `http://localhost:8082/api`

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
SECRET_KEY=your-secret-key-here
JIRA_INSTANCE=infosim.atlassian.net
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=8082
```

### Jira API Token

1. Go to your Jira account settings
2. Navigate to Security → API tokens
3. Create a new API token
4. Use your email and API token to log in to the application

## 🚀 Usage

1. **Login**: Enter your Jira email and API token on the login page
2. **Search**: Enter a Jira filter ID to search for issues
3. **View Issue**: Review issue details, hierarchy, and worklog statistics with beautiful charts
4. **Update Issue**: Set research project and chargeable status, then move to the next issue
5. **Statistics**: View time distribution across projects with interactive pie charts

## 🎨 Frontend Features

- **Modern UI**: Clean, responsive design with gradient backgrounds
- **Real-time Updates**: Instant feedback on issue updates
- **Visual Analytics**: Pie charts showing time distribution
- **Responsive Design**: Works on desktop and mobile devices
- **Type Safety**: Full TypeScript support with interfaces

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

**Backend (Flask):**
- **Application Factory Pattern**: Used in `app/__init__.py`
- **Blueprint Organization**: Routes are organized by feature
- **REST API**: All routes return JSON (no templates)
- **CORS Support**: Configured for Angular frontend
- **Service Layer**: Business logic separated from routes

**Frontend (Angular):**
- **Standalone Components**: Angular 17 standalone architecture
- **Services**: API communication layer
- **Guards**: Route protection for authentication
- **Models**: TypeScript interfaces for type safety

### Adding New Features

**Backend:**
1. Create route blueprints in `app/routes/` (return JSON)
2. Add business logic to `app/services/`
3. Register blueprints in `app/__init__.py`

**Frontend:**
1. Create components in `frontend/src/app/components/`
2. Add services in `frontend/src/app/services/`
3. Update routes in `frontend/src/app/app.routes.ts`

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues and questions, please open an issue in the repository.

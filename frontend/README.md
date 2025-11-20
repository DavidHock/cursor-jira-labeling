# Jira Labeling Frontend

Modern Angular 17 frontend for the Jira Labeling Tool.

## Development

### Prerequisites
- Node.js 20+ and npm

### Install Dependencies
```bash
npm install
```

### Run Development Server
```bash
npm start
```

The app will be available at `http://localhost:4200`

### Build for Production
```bash
npm run build
```

## Docker

The frontend is containerized with nginx. Build and run with:

```bash
docker-compose up frontend
```

The frontend will be available at `http://localhost:4200`

## Features

- **Modern UI**: Clean, responsive design with gradient backgrounds
- **Authentication**: Secure login with Jira credentials
- **Issue Management**: View and update Jira issues with research projects
- **Statistics**: Visual charts showing time distribution across projects
- **Worklog Tracking**: View recent worklogs and time spent

## Architecture

- **Standalone Components**: Uses Angular 17 standalone components
- **Services**: API service for backend communication
- **Guards**: Route guards for authentication
- **Models**: TypeScript interfaces for type safety


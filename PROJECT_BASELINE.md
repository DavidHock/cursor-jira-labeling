## Jira Labeling App Baseline

Use this as the blueprint for creating new projects that must match the current structure and feel.

---

### 1. Tech Stack
- **Frontend:** Angular 17, standalone components, SCSS styling, Angular Router, Angular HttpClient.
- **Backend:** Python 3.9, Flask 2.3 (REST only), Flask-CORS, requests for Jira API, matplotlib for charts.
- **Session/State:** Flask server-side session persisted to disk (`/shared/session_data.json`).
- **Tooling:** Docker + Docker Compose, nginx reverse proxy, Node 20 build stage for Angular.

### 2. Project Structure
```
project/
├── app/                    # Flask backend (config, routes, services, utils)
├── frontend/               # Angular app (components, services, guards, assets)
├── shared_volume/          # Shared logs + session data (mounted in Docker)
├── Dockerfile              # Backend image
├── docker-compose.yml      # Frontend + backend orchestration
├── requirements.txt        # Backend deps
├── run.py                  # Flask entry point
└── README.md               # Project overview
```

### 3. UI / UX Guidelines
- Full-screen gradient background (`#667eea → #764ba2`), cards with rounded corners and subtle shadows.
- Buttons: primary = purple gradient, secondary = muted grey, hover lifts with shadow.
- Forms: bold labels, rounded inputs, focus border in primary color.
- Issue view shows:
  - Issue metadata badges (key, assignee, time spent).
  - Description box with neutral background.
  - Research project dropdown (required) and success/error alerts.
  - Stats column: recent worklogs list, project chips, optional pie chart image.
- Responsive grid: `2fr/1fr` on desktop, stacks on mobile.

### 4. API & Authentication Pattern
- All API endpoints live under `/api` prefix with JSON responses only.
- Login stores Jira email/token/instance inside Flask session + persisted JSON file.
- Angular HttpClient calls `/api/...` (relative path) with `withCredentials: true`; nginx proxies to Flask.
- Flask-CORS configured with `supports_credentials=True` and cookie forwarding in nginx.
- Session endpoint (`GET /api/session`) gates Angular route guard for protected routes.

### 5. Deployment / Docker
- **Backend container:** Python slim image, copies `app/`, `utils/`, `run.py`, exposes port `8082`.
- **Frontend container:** Multi-stage build (Node 20 `npm install` + `ng build`, then nginx serving `/dist/frontend/browser`).
- **docker-compose:** 
  - `jira_app` (Flask) on `8082`, persistent volume `./shared_volume:/shared`.
  - `frontend` (nginx) on `4200`, proxies `/api` to `jira_app:8082`.
  - Healthcheck hits `http://localhost:8082/api/session`.
- SSL optional: Flask only uses cert/key if files exist, otherwise plain HTTP for containers.

### 6. Key Conventions & Features
- Research project dropdown pulls from fixed array; chargeable flag hidden in UI and always sends ID `10396`.
- Jira REST interactions centralized in `app/services/jira_service.py` (filter search, issue fetch, worklogs, update, watcher).
- Angular components:
  - `login` (simple form)
  - `search` (filter ID form)
  - `issue-view` (full issue hierarchy + stats + update workflow)
- Route guard hits `/api/session`; unauthorized redirects to `/login`.
- API routes (`auth`, `search`, `issues`, `update`) separated into blueprints.
- Logging to `/shared/app.log`, updated issues log at `/shared/updated_issues.log`.

Use this baseline to ensure future projects maintain identical architecture, styling, and behavior. Adjust only the business-specific content while keeping the structure intact.




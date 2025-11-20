# Jira API Interactions - Complete Documentation

This document lists all files and code sections where the application interacts with Jira's REST API.

## Summary

The application makes **6 different types of Jira REST API calls** across **1 main service file** and **3 route files**.

---

## Main Service File: `app/services/jira_service.py`

This is the primary file containing all Jira API interactions.

### 1. **GET Filter by ID** (Line 257-277)
**Function:** `get_jql_from_filter()`
**API Endpoint:** `GET https://{jira_instance}/rest/api/3/filter/{filter_id}`
**Purpose:** Retrieves the JQL query from a saved Jira filter
**Called by:** `search_issue_by_filter()`

```python
# Line 259
filter_url = f"https://{jira_instance}/rest/api/3/filter/{filter_id}"
# Line 264
response = requests.get(filter_url, headers=headers, auth=auth, timeout=30)
```

**Headers:**
- `Accept: application/json`
- `Authorization: HTTPBasicAuth(email, api_token)`

---

### 2. **POST Search Issues by JQL** (Line 280-322)
**Function:** `search_issue_by_filter()`
**API Endpoint:** `POST https://{jira_instance}/rest/api/3/search/jql`
**Purpose:** Searches for issues using a JQL query from a filter
**Called by:** 
- `app/routes/search.py` (line 26)
- `app/routes/update.py` (line 61)

```python
# Line 293
search_url = f"https://{jira_instance}/rest/api/3/search/jql"
# Line 306
response = requests.post(
    search_url, headers=headers, auth=auth, json=payload, timeout=30
)
```

**Payload:**
```json
{
  "jql": "<jql_query_from_filter>",
  "maxResults": 1,
  "fields": ["key"]
}
```

**Headers:**
- `Accept: application/json`
- `Content-Type: application/json`
- `Authorization: HTTPBasicAuth(email, api_token)`

---

### 3. **GET Issue with Hierarchy** (Line 155-254)
**Function:** `get_issue_hierarchy()`
**API Endpoint:** `GET https://{jira_instance}/rest/api/3/issue/{issue_key}?expand=renderedFields,worklog`
**Purpose:** Fetches a single issue and recursively fetches all linked issues (parent, inward, outward links)
**Called by:** `app/routes/issues.py` (line 32)

```python
# Line 178
response = requests.get(
    f"https://{jira_instance}/rest/api/3/issue/{current_issue_key}?expand=renderedFields,worklog",
    headers=headers,
    auth=auth,
    timeout=30
)
```

**Query Parameters:**
- `expand=renderedFields,worklog` - Expands worklog data and rendered fields

**Headers:**
- `Accept: application/json`
- `Authorization: HTTPBasicAuth(email, api_token)`

**Fields Extracted:**
- `summary` (issue name)
- `description` (nested JSON structure)
- `assignee.displayName` and `assignee.accountId`
- `worklog.worklogs[]` (time spent)
- `customfield_10097` (research project)
- `parent` (parent issue)
- `issuelinks[]` (linked issues)

---

### 4. **GET Worklogs by Assignee** (Line 46-109)
**Function:** `get_recent_worklogs()`
**API Endpoint:** `GET https://{jira_instance}/rest/api/3/search?jql={jql}&fields=summary,worklog,customfield_10097`
**Purpose:** Fetches all worklogs for a specific assignee in the last 14 days
**Called by:** `app/routes/issues.py` (line 49)

```python
# Line 57-61
jql_query = f"worklogAuthor = {assignee_id} AND worklogDate >= -14d"
url = (
    f"https://{jira_instance}/rest/api/3/search?"
    f"jql={jql_query}&fields=summary,worklog,{Config.CUSTOM_FIELD_RESEARCH_PROJECT}"
)
# Line 67
response = requests.get(url, headers=headers, auth=auth, timeout=30)
```

**JQL Query:**
```
worklogAuthor = {assignee_id} AND worklogDate >= -14d
```

**Query Parameters:**
- `jql` - JQL query string
- `fields` - Comma-separated list: `summary,worklog,customfield_10097`

**Headers:**
- `Accept: application/json`
- `Authorization: HTTPBasicAuth(email, api_token)`

**Data Processed:**
- Aggregates time spent per research project
- Returns list of worklog issues with time spent

---

### 5. **PUT Update Issue** (Line 325-369)
**Function:** `update_issue()`
**API Endpoint:** `PUT https://{jira_instance}/rest/api/3/issue/{issue_key}`
**Purpose:** Updates an issue's research project and chargeable status
**Called by:** `app/routes/update.py` (line 39)

```python
# Line 340
url = f"https://{jira_instance}/rest/api/3/issue/{issue_key}"
# Line 348
response = requests.put(url, json=update_data, auth=auth, headers=headers, timeout=30)
```

**Payload:**
```json
{
  "fields": {
    "customfield_10097": {
      "value": "<research_project>"
    },
    "customfield_10384": {
      "id": "<chargeable_id>"
    }
  }
}
```

**Note:** `customfield_10384` is only included if `chargeable` parameter is provided.

**Headers:**
- `Accept: application/json`
- `Content-Type: application/json`
- `Authorization: HTTPBasicAuth(email, api_token)`

**Expected Response:** `204 No Content` (success)

**Custom Fields:**
- `customfield_10097` - Research Project (required)
- `customfield_10384` - Chargeable status (optional)

---

### 6. **POST Add Watcher** (Line 372-395)
**Function:** `add_watcher()`
**API Endpoint:** `POST https://{jira_instance}/rest/api/3/issue/{issue_key}/watchers`
**Purpose:** Adds the current user as a watcher to an issue
**Called by:** `app/routes/update.py` (line 52)

```python
# Line 374
watcher_url = f"https://{jira_instance}/rest/api/3/issue/{issue_key}/watchers"
# Line 379
watcher_response = requests.post(
    watcher_url,
    data=json.dumps(email),
    auth=auth,
    headers=headers,
    timeout=30
)
```

**Payload:**
- Raw JSON string of the user's email address

**Headers:**
- `Content-Type: application/json`
- `Authorization: HTTPBasicAuth(email, api_token)`

**Expected Responses:**
- `204 No Content` - Success
- `400 Bad Request` - User is already a watcher (treated as success)

---

## Route Files That Call Jira Services

### `app/routes/issues.py`

**Route:** `GET /api/fetch_issue`

**Jira API Calls Made:**
1. **Line 32-37:** `get_issue_hierarchy()` 
   - Fetches issue and all linked issues
   - API: `GET /rest/api/3/issue/{issue_key}?expand=renderedFields,worklog`

2. **Line 49-54:** `get_recent_worklogs()`
   - Fetches worklogs for assignee (last 14 days)
   - API: `GET /rest/api/3/search?jql=...`

**Flow:**
```
User Request → fetch_issue() → get_issue_hierarchy() → Jira API
                              → get_recent_worklogs() → Jira API
                              → generate_pie_chart() (local processing)
                              → Return JSON response
```

---

### `app/routes/search.py`

**Route:** `POST /api/search_issue`

**Jira API Calls Made:**
1. **Line 26-31:** `search_issue_by_filter()`
   - Internally calls `get_jql_from_filter()` → `GET /rest/api/3/filter/{filter_id}`
   - Then calls `POST /rest/api/3/search/jql`

**Flow:**
```
User Request → search_issue() → search_issue_by_filter()
                                → get_jql_from_filter() → GET /rest/api/3/filter/{id}
                                → POST /rest/api/3/search/jql
                                → Return issue_key and total_issues
```

---

### `app/routes/update.py`

**Route:** `POST /api/update_issue`

**Jira API Calls Made:**
1. **Line 39-46:** `update_issue()`
   - Updates issue fields
   - API: `PUT /rest/api/3/issue/{issue_key}`

2. **Line 52-57:** `add_watcher()`
   - Adds user as watcher
   - API: `POST /rest/api/3/issue/{issue_key}/watchers`

3. **Line 61-66:** `search_issue_by_filter()`
   - Gets next issue from filter
   - API: `GET /rest/api/3/filter/{filter_id}` → `POST /rest/api/3/search/jql`

**Flow:**
```
User Request → update_issue_route()
              → update_issue() → PUT /rest/api/3/issue/{key}
              → add_watcher() → POST /rest/api/3/issue/{key}/watchers
              → search_issue_by_filter() → GET filter → POST search
              → Return next_issue and total_issues
```

---

## Configuration File: `app/config.py`

**Jira-Related Configuration (Lines 15-28):**

```python
# Line 16
JIRA_INSTANCE = os.environ.get("JIRA_INSTANCE", "infosim.atlassian.net")

# Line 24-25: Custom Field IDs
CUSTOM_FIELD_RESEARCH_PROJECT = "customfield_10097"
CUSTOM_FIELD_CHARGEABLE = "customfield_10384"

# Line 28: Default Filter ID
DEFAULT_FILTER_ID = "10456"
```

---

## Authentication

All Jira API calls use **HTTP Basic Authentication**:
- **Username:** User's Jira email address
- **Password:** User's Jira API token
- **Implementation:** `requests.auth.HTTPBasicAuth(email, api_token)`

**Session Storage:**
- Stored in Flask session: `session["jira_email"]`, `session["jira_api_token"]`, `session["jira_instance"]`
- Persisted to `/shared/session_data.json` via `app/services/session_service.py`

---

## API Endpoints Summary

| Method | Endpoint | Purpose | Called From |
|--------|----------|---------|--------------|
| GET | `/rest/api/3/filter/{filter_id}` | Get JQL from saved filter | `get_jql_from_filter()` |
| POST | `/rest/api/3/search/jql` | Search issues by JQL | `search_issue_by_filter()` |
| GET | `/rest/api/3/issue/{issue_key}?expand=renderedFields,worklog` | Get issue details | `get_issue_hierarchy()` |
| GET | `/rest/api/3/search?jql=...&fields=...` | Get worklogs by assignee | `get_recent_worklogs()` |
| PUT | `/rest/api/3/issue/{issue_key}` | Update issue fields | `update_issue()` |
| POST | `/rest/api/3/issue/{issue_key}/watchers` | Add watcher to issue | `add_watcher()` |

---

## Custom Fields Used

- **`customfield_10097`** - Research Project (dropdown/select field)
- **`customfield_10384`** - Chargeable status (option ID field)

---

## Error Handling

All API calls include:
- **Timeout:** 30 seconds
- **Try/Except:** Catches `requests.exceptions.RequestException`
- **Logging:** Errors logged with status codes and response text
- **Graceful Degradation:** Functions return `None`, empty lists, or error dictionaries on failure

---

## Notes

- The `get_issue_hierarchy()` function recursively fetches linked issues, which can result in multiple API calls per request
- Worklog queries are limited to the last 14 days
- Search queries are limited to `maxResults: 1` to get only the first matching issue
- All API calls use Jira REST API v3 (`/rest/api/3/`)


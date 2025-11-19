import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # ✅ Force Matplotlib to use a non-GUI backend
import matplotlib.pyplot as plt
from collections import defaultdict
import io
import base64
import logging


CUSTOM_FIELD_ID = "customfield_10097"  # Updated with actual custom field ID


def get_issue_links(issue_data):
    """Extracts all linked issues and categorizes them."""
    issue_links = []
    
    if 'parent' in issue_data['fields']:
        issue_links.append({
            'key': issue_data['fields']['parent']['key'],
            'link_type': 'Parent'
        })
    
    if 'issuelinks' in issue_data['fields']:
        for link in issue_data['fields']['issuelinks']:
            if 'inwardIssue' in link:
                issue_links.append({
                    'key': link['inwardIssue']['key'],
                    'link_type': f"Inward: {link['type']['inward']}"
                })
            if 'outwardIssue' in link:
                issue_links.append({
                    'key': link['outwardIssue']['key'],
                    'link_type': f"Outward: {link['type']['outward']}"
                })
    
    return issue_links

def get_recent_worklogs(assignee_id, email, api_token, jira_instance):
    """
    Fetch all worklogs for a given assignee in the last 14 days.
    """
    if not assignee_id:
        logging.warning("No valid assignee ID found, skipping worklog lookup.")
        return [], {}

    logging.debug(f"Fetching worklogs for Assignee ID: {assignee_id}")

    jql_query = f"worklogAuthor = {assignee_id} AND worklogDate >= -14d"
    url = f"https://{jira_instance}/rest/api/3/search?jql={jql_query}&fields=summary,worklog,{CUSTOM_FIELD_ID}"

    auth = HTTPBasicAuth(email, api_token)
    headers = {"Accept": "application/json"}

    response = requests.get(url, headers=headers, auth=auth)

    worklog_data = {}
    worklog_issues = []

    if response.status_code == 200:
        issues = response.json().get("issues", [])

        for issue in issues:
            issue_key = issue.get("key", "Unknown Issue")
            project_data = issue.get("fields", {}).get(CUSTOM_FIELD_ID, {})
            project = project_data.get("value", "Unknown Project") if isinstance(project_data, dict) else str(project_data)

            worklogs = issue.get("fields", {}).get("worklog", {}).get("worklogs", [])
            total_time_spent = sum(wl.get("timeSpentSeconds", 0) / 3600 for wl in worklogs)

            worklog_data[project] = worklog_data.get(project, 0) + total_time_spent

            worklog_issues.append({
                "key": issue_key,
                "name": issue.get("fields", {}).get("summary", "No Title"),
                "research_project": project,
                "time_spent_hours": round(total_time_spent, 2)
            })

        logging.debug(f"Worklogs Retrieved: {worklog_data}")

    else:
        logging.error(f"Failed to fetch worklogs, Status Code: {response.status_code}")

    return worklog_issues, worklog_data



def generate_pie_chart(time_spent_by_project):
    """Generates a pie chart of time spent per research project and returns it as a base64 string."""
    labels = list(time_spent_by_project.keys())
    values = list(time_spent_by_project.values())
    
    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title("Time Spent per Research Project (Last 14 Days)")
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode('utf8')

def extract_plain_text_from_description(description_data):
    """
    Extracts plain text from the Jira description field, which is a nested JSON structure.
    """
    if not isinstance(description_data, dict):
        return "No description available"
    
    text_content = []

    # Jira descriptions are usually in 'content' -> list of elements with 'text' field
    def traverse_content(content):
        for element in content:
            if element.get("type") == "text":
                text_content.append(element.get("text", ""))
            elif "content" in element:
                traverse_content(element["content"])

    traverse_content(description_data.get("content", []))
    return " ".join(text_content).strip() or "No description available"

def get_issue_hierarchy(issue_key, email, api_token, jira_instance):
    auth = HTTPBasicAuth(email, api_token)
    headers = {"Accept": "application/json"}

    issues = []
    visited_issues = set()
    queue = [(issue_key, "Self")]  # Queue for BFS-like traversal

    while queue:
        current_issue_key, link_type = queue.pop(0)

        if current_issue_key in visited_issues:
            continue
        visited_issues.add(current_issue_key)

        logging.debug(f"Fetching issue -> {current_issue_key}")

        response = requests.get(f"https://{jira_instance}/rest/api/3/issue/{current_issue_key}?expand=renderedFields,worklog", headers=headers, auth=auth)
        
        if response.status_code != 200:
            logging.error(f"Failed to fetch issue {current_issue_key}, Status Code: {response.status_code}")
            continue
        
        issue_data = response.json()
        
        # Extract issue fields
        issue_name = issue_data['fields'].get('summary', 'No Title')
        raw_description = issue_data['fields'].get('description', {})
        issue_description = extract_plain_text_from_description(raw_description)

        assignee_data = issue_data['fields'].get('assignee')
        assignee_name = assignee_data.get('displayName', 'Unassigned') if assignee_data else 'Unassigned'
        assignee_id = assignee_data.get('accountId', None) if assignee_data else None  # FIXED

        logging.debug(f"Issue {current_issue_key} Assignee Name -> {assignee_name}")
        logging.debug(f"Issue {current_issue_key} Assignee ID -> {assignee_id}")

        worklogs = issue_data['fields'].get('worklog', {}).get('worklogs', [])
        issue_timespent = sum(wl.get("timeSpentSeconds", 0) / 3600 for wl in worklogs)
        logging.debug(f"Issue {current_issue_key} Time Spent -> {round(issue_timespent, 2)} hours")

        research_project_field = issue_data['fields'].get(CUSTOM_FIELD_ID)
        research_project = research_project_field.get('value') if isinstance(research_project_field, dict) else 'N/A'
        logging.debug(f"Issue {current_issue_key} Research Project -> {research_project}")

        issues.append({
            'key': current_issue_key,
            'name': issue_name,
            'description': issue_description,
            'assignee_name': assignee_name,  # FIXED
            'assignee_id': assignee_id,  # FIXED
            'timespent': round(issue_timespent, 2),
            'research_project': research_project,
            'link_type': link_type
        })

        # Get linked issues (using external `get_issue_links` function)
        issue_links = get_issue_links(issue_data)
        for linked_issue in issue_links:
            queue.append((linked_issue['key'], linked_issue['link_type']))  # Add linked issue to queue
    
    logging.debug("Completed issue hierarchy retrieval")
    return issues




def get_jql_from_filter(filter_id, email, api_token, jira_instance):
    """ Holt die JQL-Abfrage eines gespeicherten Filters anhand der ID """
    filter_url = f"https://{jira_instance}/rest/api/3/filter/{filter_id}"
    auth = HTTPBasicAuth(email, api_token)
    headers = {"Accept": "application/json"}

    response = requests.get(filter_url, headers=headers, auth=auth)

    if response.status_code == 200:
        return response.json().get("jql")
    else:
        print(f"Fehler beim Abrufen des Filters {filter_id}: {response.status_code}, {response.text}")
        return None


def search_issue_by_filter(filter_id, email, api_token, jira_instance):
    """ Sucht Issues basierend auf der JQL-Abfrage eines gespeicherten Filters """
    jql = get_jql_from_filter(filter_id, email, api_token, jira_instance)
    print("I was here")

    if not jql:
        print(f"Fehler: Der gespeicherte Filter mit ID {filter_id} konnte nicht geladen werden.")
        return None
    search_url = f"https://{jira_instance}/rest/api/3/search/jql"
    auth = HTTPBasicAuth(email, api_token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    payload = {
        "jql": jql,
        "maxResults": 1,
        "fields": ["key"]
    }

    response = requests.post(search_url, headers=headers, auth=auth, json=payload)
    
    if response.status_code == 200:
        issues = response.json().get('issues', [])
        total_issues = len(issues)  # ❗ Fix: Anzahl der gefundenen Issues zählen
        return (issues[0]['key'], total_issues) if issues else (None, 0)  # ❗ Fix: Immer beides zurückgeben
    
    return None, 0  # ❗ Falls API-Fehler oder kein Issue gefunden wurde

def get_assignee_name(account_id, email, api_token, jira_instance):
    """Fetches the assignee's display name using their Jira account ID."""
    if not account_id or not isinstance(account_id, str):
        return "Unassigned"

    url = f"https://{jira_instance}/rest/api/3/user?accountId={account_id}"
    auth = HTTPBasicAuth(email, api_token)
    headers = {"Accept": "application/json"}

    response = requests.get(url, headers=headers, auth=auth)

    if response.status_code == 200:
        return response.json().get("displayName", "Unassigned")
    
    return "Unassigned"

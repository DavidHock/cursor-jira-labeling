"""
Jira API service layer for interacting with Jira REST API.
"""
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import matplotlib
matplotlib.use("Agg")  # Force Matplotlib to use a non-GUI backend
import matplotlib.pyplot as plt
from collections import defaultdict
import io
import base64
import json
import logging
from urllib.parse import quote
from app.config import Config

logger = logging.getLogger(__name__)


def get_issue_links(issue_data):
    """Extract all linked issues and categorize them."""
    issue_links = []
    
    if "parent" in issue_data["fields"]:
        issue_links.append({
            "key": issue_data["fields"]["parent"]["key"],
            "link_type": "Parent"
        })
    
    if "issuelinks" in issue_data["fields"]:
        for link in issue_data["fields"]["issuelinks"]:
            if "inwardIssue" in link:
                issue_links.append({
                    "key": link["inwardIssue"]["key"],
                    "link_type": f"Inward: {link['type']['inward']}"
                })
            if "outwardIssue" in link:
                issue_links.append({
                    "key": link["outwardIssue"]["key"],
                    "link_type": f"Outward: {link['type']['outward']}"
                })
    
    return issue_links


def get_recent_worklogs(assignee_id, email, api_token, jira_instance):
    """
    Fetch all worklogs for a given assignee in the last 14 days.
    Returns tuple of (worklog_issues, worklog_data_dict).
    """
    if not assignee_id:
        logger.warning("No valid assignee ID found, skipping worklog lookup.")
        return [], {}
    
    logger.info(f"[WORKLOGS] Fetching worklogs for Assignee ID: {assignee_id}")
    
    jql_query = f"worklogAuthor = {assignee_id} AND worklogDate >= -14d"
    url = f"https://{jira_instance}/rest/api/3/search/jql"
    
    auth = HTTPBasicAuth(email, api_token)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "jql": jql_query,
        "maxResults": 1000,  # Get up to 1000 issues with worklogs
        "fields": ["summary", Config.CUSTOM_FIELD_RESEARCH_PROJECT]
    }
    
    logger.info(f"[WORKLOGS] Making POST request to: {url}")
    logger.info(f"[WORKLOGS] JQL query: {jql_query}")
    
    try:
        response = requests.post(url, headers=headers, auth=auth, json=payload, timeout=30)
        
        worklog_data = {}
        worklog_issues = []
        
        logger.info(f"[WORKLOGS] Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            issues = data.get("issues", [])
            logger.info(f"[WORKLOGS] Found {len(issues)} issues with worklogs")
            
            # Handle pagination if needed
            next_page_token = data.get("nextPageToken")
            is_last = data.get("isLast", True)
            
            if not is_last and next_page_token:
                logger.warning(f"[WORKLOGS] More than 1000 issues with worklogs found, only processing first 1000")
            
            for issue in issues:
                issue_key = issue.get("key", "Unknown Issue")
                project_data = issue.get("fields", {}).get(Config.CUSTOM_FIELD_RESEARCH_PROJECT, {})
                project = (
                    project_data.get("value", "Unknown Project")
                    if isinstance(project_data, dict)
                    else str(project_data)
                )
                
                # Fetch worklogs separately for each issue as search API doesn't return full worklog data
                total_time_spent = 0
                try:
                    worklog_url = f"https://{jira_instance}/rest/api/3/issue/{issue_key}/worklog"
                    worklog_response = requests.get(worklog_url, headers=headers, auth=auth, timeout=30)
                    if worklog_response.status_code == 200:
                        worklog_data_full = worklog_response.json()
                        all_worklogs = worklog_data_full.get("worklogs", [])
                        
                        # Filter worklogs from last 14 days and by the assignee
                        cutoff_date = datetime.now() - timedelta(days=14)
                        
                        for wl in all_worklogs:
                            # Check if worklog is from the assignee and within 14 days
                            wl_author_id = wl.get("author", {}).get("accountId", "")
                            wl_started = wl.get("started", "")
                            
                            if wl_author_id == assignee_id and wl_started:
                                try:
                                    wl_date = datetime.fromisoformat(wl_started.replace("Z", "+00:00"))
                                    if wl_date >= cutoff_date:
                                        total_time_spent += wl.get("timeSpentSeconds", 0) / 3600
                                except:
                                    # If date parsing fails, include it anyway
                                    total_time_spent += wl.get("timeSpentSeconds", 0) / 3600
                except Exception as e:
                    logger.warning(f"Failed to fetch worklogs for {issue_key}: {e}")
                
                if total_time_spent > 0:
                    worklog_data[project] = worklog_data.get(project, 0) + total_time_spent
                    
                    worklog_issues.append({
                        "key": issue_key,
                        "name": issue.get("fields", {}).get("summary", "No Title"),
                        "research_project": project,
                        "time_spent_hours": round(total_time_spent, 2)
                    })
            
            logger.info(f"[WORKLOGS] Worklogs Retrieved: {worklog_data}, Total issues: {len(worklog_issues)}")
        else:
            logger.error(
                f"[WORKLOGS] Failed to fetch worklogs, Status Code: {response.status_code}, "
                f"Response: {response.text}"
            )
        
        return worklog_issues, worklog_data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"[WORKLOGS] Error fetching worklogs: {e}", exc_info=True)
        return [], {}


def generate_pie_chart(time_spent_by_project):
    """
    Generate a pie chart of time spent per research project.
    Returns base64-encoded image string.
    """
    if not time_spent_by_project:
        return None
    
    labels = list(time_spent_by_project.keys())
    values = list(time_spent_by_project.values())
    
    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=140)
    plt.title("Time Spent per Research Project (Last 14 Days)")
    
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode("utf8")


def extract_plain_text_from_description(description_data):
    """
    Extract plain text from the Jira description field,
    which is a nested JSON structure.
    """
    if not isinstance(description_data, dict):
        return "No description available"
    
    text_content = []
    
    def traverse_content(content):
        for element in content:
            if element.get("type") == "text":
                text_content.append(element.get("text", ""))
            elif "content" in element:
                traverse_content(element["content"])
    
    traverse_content(description_data.get("content", []))
    return " ".join(text_content).strip() or "No description available"


def get_issue_hierarchy(issue_key, email, api_token, jira_instance):
    """
    Fetch a Jira issue and all its linked issues (hierarchy).
    Returns a list of issue dictionaries.
    """
    auth = HTTPBasicAuth(email, api_token)
    headers = {"Accept": "application/json"}
    
    issues = []
    visited_issues = set()
    queue = [(issue_key, "Self")]
    
    while queue:
        current_issue_key, link_type = queue.pop(0)
        
        if current_issue_key in visited_issues:
            continue
        visited_issues.add(current_issue_key)
        
        logger.debug(f"Fetching issue -> {current_issue_key}")
        
        try:
            response = requests.get(
                f"https://{jira_instance}/rest/api/3/issue/{current_issue_key}?expand=renderedFields,worklog",
                headers=headers,
                auth=auth,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(
                    f"Failed to fetch issue {current_issue_key}, "
                    f"Status Code: {response.status_code}, Response: {response.text}"
                )
                continue
            
            issue_data = response.json()
            
            # Extract issue fields
            issue_name = issue_data["fields"].get("summary", "No Title")
            raw_description = issue_data["fields"].get("description", {})
            issue_description = extract_plain_text_from_description(raw_description)
            
            assignee_data = issue_data["fields"].get("assignee")
            assignee_name = (
                assignee_data.get("displayName", "Unassigned")
                if assignee_data
                else "Unassigned"
            )
            assignee_id = (
                assignee_data.get("accountId", None) if assignee_data else None
            )
            
            logger.debug(
                f"Issue {current_issue_key} Assignee Name -> {assignee_name}, "
                f"Assignee ID -> {assignee_id}"
            )
            
            worklogs = issue_data["fields"].get("worklog", {}).get("worklogs", [])
            issue_timespent = sum(
                wl.get("timeSpentSeconds", 0) / 3600 for wl in worklogs
            )
            
            logger.debug(
                f"Issue {current_issue_key} Time Spent -> {round(issue_timespent, 2)} hours"
            )
            
            research_project_field = issue_data["fields"].get(Config.CUSTOM_FIELD_RESEARCH_PROJECT)
            research_project = (
                research_project_field.get("value")
                if isinstance(research_project_field, dict)
                else "N/A"
            )
            
            logger.debug(
                f"Issue {current_issue_key} Research Project -> {research_project}"
            )
            
            issues.append({
                "key": current_issue_key,
                "name": issue_name,
                "description": issue_description,
                "assignee_name": assignee_name,
                "assignee_id": assignee_id,
                "timespent": round(issue_timespent, 2),
                "research_project": research_project,
                "link_type": link_type
            })
            
            # Get linked issues
            issue_links = get_issue_links(issue_data)
            for linked_issue in issue_links:
                queue.append((linked_issue["key"], linked_issue["link_type"]))
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching issue {current_issue_key}: {e}")
            continue
    
    logger.debug("Completed issue hierarchy retrieval")
    return issues


def get_jql_from_filter(filter_id, email, api_token, jira_instance):
    """Get the JQL query from a saved Jira filter by filter ID."""
    filter_url = f"https://{jira_instance}/rest/api/3/filter/{filter_id}"
    auth = HTTPBasicAuth(email, api_token)
    headers = {"Accept": "application/json"}
    
    try:
        response = requests.get(filter_url, headers=headers, auth=auth, timeout=30)
        
        if response.status_code == 200:
            return response.json().get("jql")
        else:
            logger.error(
                f"Error fetching filter {filter_id}: "
                f"{response.status_code}, {response.text}"
            )
            return None
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching filter {filter_id}: {e}")
        return None


def search_issue_by_filter(filter_id, email, api_token, jira_instance):
    """
    Search for issues based on a saved Jira filter.
    Returns tuple of (issue_key, total_issues_count).
    """
    logger.info(f"[SEARCH] Starting search_issue_by_filter with filter_id={filter_id}")
    jql = get_jql_from_filter(filter_id, email, api_token, jira_instance)
    
    if not jql:
        logger.error(
            f"Error: Could not load saved filter with ID {filter_id}."
        )
        return None, 0
    
    logger.info(f"[SEARCH] JQL query retrieved: {jql[:100]}..." if len(jql) > 100 else f"[SEARCH] JQL query retrieved: {jql}")
    
    auth = HTTPBasicAuth(email, api_token)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Get total count by paginating through results
    # The old GET /search endpoint is deprecated (returns 410)
    # The new POST /search/jql endpoint doesn't return 'total' field
    # We need to count by making paginated requests
    count_url = f"https://{jira_instance}/rest/api/3/search/jql"
    total_issues = 0
    max_count_requests = 100  # Limit to prevent infinite loops, max 100,000 issues
    max_results_per_page = 1000
    
    logger.info(f"[SEARCH] Counting total issues by pagination (max {max_count_requests * max_results_per_page} issues)")
    try:
        next_page_token = None
        request_count = 0
        
        while request_count < max_count_requests:
            count_payload = {
                "jql": jql,
                "maxResults": max_results_per_page,
                "fields": ["key"]  # Only fetch key field for counting
            }
            if next_page_token:
                count_payload["nextPageToken"] = next_page_token
            
            count_response = requests.post(
                count_url,
                headers=headers,
                auth=auth,
                json=count_payload,
                timeout=30
            )
            
            if count_response.status_code == 200:
                count_data = count_response.json()
                issues = count_data.get("issues", [])
                total_issues += len(issues)
                is_last = count_data.get("isLast", True)
                next_page_token = count_data.get("nextPageToken")
                
                logger.info(f"[SEARCH] Count request {request_count + 1}: found {len(issues)} issues, total so far: {total_issues}, isLast: {is_last}")
                
                if is_last or not next_page_token:
                    break
                
                request_count += 1
            else:
                logger.warning(f"[SEARCH] Failed to get count page {request_count + 1}: {count_response.status_code}, {count_response.text}")
                break
        
        logger.info(f"[SEARCH] Total issues counted: {total_issues}")
    except Exception as e:
        logger.error(f"[SEARCH] Failed to count issues: {e}", exc_info=True)
    
    # Now get the first issue using POST /search/jql (original working method)
    search_url = f"https://{jira_instance}/rest/api/3/search/jql"
    payload = {
        "jql": jql,
        "maxResults": 1,
        "fields": ["key"]
    }
    
    logger.info(f"[SEARCH] Making POST request to search URL: {search_url}")
    logger.info(f"[SEARCH] POST payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            search_url,
            headers=headers,
            auth=auth,
            json=payload,
            timeout=30
        )
        
        logger.info(f"[SEARCH] POST response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"[SEARCH] POST response data keys: {list(data.keys())}")
            logger.info(f"[SEARCH] POST response full data: {json.dumps(data, indent=2)}")
            issues = data.get("issues", [])
            # Get total from POST response (check both 'total' and 'maxResults' fields)
            post_total = data.get("total", 0)
            # Also check if total is in a different location
            if post_total == 0:
                # Some Jira API versions might return total differently
                post_total = data.get("maxResults", 0)  # This won't work, but let's check
            logger.info(f"[SEARCH] POST response total field: {post_total}")
            
            # Priority: 1) Count query total, 2) POST response total, 3) Keep 0 if both failed
            if total_issues > 0:
                logger.info(f"[SEARCH] Using total from count query: {total_issues}")
            elif post_total > 0:
                total_issues = post_total
                logger.info(f"[SEARCH] Using total from POST response: {total_issues}")
            else:
                logger.warning(f"[SEARCH] WARNING: Both count query and POST returned 0 for total!")
                logger.warning(f"[SEARCH] Count query returned: {total_issues}, POST returned: {post_total}")
                logger.warning(f"[SEARCH] This means the Jira API is not returning the total count correctly")
            
            logger.info(f"[SEARCH] Search returned {len(issues)} issues, final total={total_issues}")
            issue_key = issues[0]["key"] if issues else None
            logger.info(f"[SEARCH] Returning issue_key={issue_key}, total_issues={total_issues}")
            return (issue_key, total_issues) if issues else (None, 0)
        
        logger.error(
            f"Error searching issues: {response.status_code}, {response.text}"
        )
        return None, 0
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching issues: {e}")
        return None, 0


def update_issue(issue_key, research_project, chargeable, email, api_token, jira_instance):
    """
    Update a Jira issue with research project and chargeable status.
    Returns tuple of (success: bool, response_data: dict).
    """
    update_data = {
        "fields": {
            Config.CUSTOM_FIELD_RESEARCH_PROJECT: {"value": research_project}
        }
    }
    
    # Only add chargeable field if provided
    if chargeable:
        update_data["fields"][Config.CUSTOM_FIELD_CHARGEABLE] = {"id": chargeable}
    
    url = f"https://{jira_instance}/rest/api/3/issue/{issue_key}"
    auth = HTTPBasicAuth(email, api_token)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.put(url, json=update_data, auth=auth, headers=headers, timeout=30)
        
        if response.status_code == 204:
            return True, {"message": "Issue updated successfully"}
        else:
            logger.error(
                f"Failed to update issue {issue_key}: "
                f"{response.status_code} - {response.text}"
            )
            return False, {
                "message": "Failed to update issue.",
                "jira_response": response.text,
                "status_code": response.status_code
            }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating issue {issue_key}: {e}")
        return False, {
            "message": "Error updating issue.",
            "error": str(e),
            "status_code": 500
        }


def add_watcher(issue_key, email, api_token, jira_instance):
    """Add the current user as a watcher to a Jira issue."""
    auth = HTTPBasicAuth(email, api_token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    try:
        # First, get the user's accountId
        user_url = f"https://{jira_instance}/rest/api/3/myself"
        user_response = requests.get(user_url, headers=headers, auth=auth, timeout=30)
        
        if user_response.status_code != 200:
            logger.warning(f"Failed to get user info: {user_response.status_code}")
            return
        
        account_id = user_response.json().get("accountId")
        if not account_id:
            logger.warning("Could not get accountId for watcher")
            return
        
        # Add watcher using accountId
        watcher_url = f"https://{jira_instance}/rest/api/3/issue/{issue_key}/watchers"
        watcher_response = requests.post(
            watcher_url,
            json=account_id,  # Jira API expects accountId as JSON
            auth=auth,
            headers=headers,
            timeout=30
        )
        
        if watcher_response.status_code not in [204, 400]:
            # 400 if user is already a watcher
            logger.warning(
                f"Failed to add watcher: {watcher_response.status_code} - "
                f"{watcher_response.text}"
            )
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error adding watcher: {e}")


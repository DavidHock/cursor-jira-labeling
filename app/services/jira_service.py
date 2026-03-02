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

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.config import Config

logger = logging.getLogger(__name__)


def _make_request(url, method="GET", auth=None, headers=None, json=None, timeout=30, max_retries=3):
    """
    Helper to make HTTP requests with retry logic and exponential backoff.
    Honors Retry-After header for 429 errors.
    """
    # Sanitize auth if provided
    if auth:
        auth = HTTPBasicAuth(auth.username.strip(), auth.password.strip())
    
    # Mask token for logging: "ATATT...last4"
    token_masked = "None"
    if auth and auth.password:
        p = auth.password
        token_masked = f"{p[:5]}...{p[-4:]}" if len(p) > 10 else "***"
    
    logger.debug(f"[_make_request] {method} {url}")
    logger.debug(f"[_make_request] Auth User: {auth.username if auth else 'None'}, Token: {token_masked}")

    retry_count = 0
    response = None
    while retry_count <= max_retries:
        try:
            if method == "GET":
                response = requests.get(url, auth=auth, headers=headers, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, auth=auth, headers=headers, json=json, timeout=timeout)
            elif method == "PUT":
                response = requests.put(url, auth=auth, headers=headers, json=json, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 2 * (retry_count + 1)))
                logger.warning(f"Rate limited (429). Retrying in {retry_after}s... (Attempt {retry_count + 1}/{max_retries})")
                time.sleep(retry_after)
                retry_count += 1
                continue

            if response.status_code >= 500:
                backoff = 2 ** retry_count
                logger.warning(f"Server error ({response.status_code}). Retrying in {backoff}s... (Attempt {retry_count + 1}/{max_retries})")
                time.sleep(backoff)
                retry_count += 1
                continue

            return response

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            backoff = 2 ** retry_count
            logger.warning(f"Network error: {e}. Retrying in {backoff}s... (Attempt {retry_count + 1}/{max_retries})")
            time.sleep(backoff)
            retry_count += 1

    # If we fall through, return the last response or raise if no response
    if response is None:
        raise requests.exceptions.RequestException("Max retries exceeded without response")
    return response


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
    jira_instance = jira_instance.strip()
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
    
    response = _make_request(url, method="POST", headers=headers, auth=auth, json=payload)
    
    worklog_data = {}
    worklog_issues = []
    
    logger.info(f"[WORKLOGS] Response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        issues = data.get("issues", [])
        logger.info(f"[WORKLOGS] Found {len(issues)} issues with worklogs")
        
        # Internal helper to fetch worklogs for an issue
        def fetch_issue_worklogs(issue):
            issue_key = issue.get("key", "Unknown Issue")
            try:
                worklog_url = f"https://{jira_instance}/rest/api/3/issue/{issue_key}/worklog"
                wl_resp = _make_request(worklog_url, headers=headers, auth=auth)
                if wl_resp.status_code == 200:
                    return issue_key, wl_resp.json()
            except Exception as e:
                logger.warning(f"Failed to fetch worklogs for {issue_key}: {e}")
            return issue_key, None

        # Fetch worklogs in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_issue = {executor.submit(fetch_issue_worklogs, issue): issue for issue in issues}
            
            worklog_results = {}
            for future in as_completed(future_to_issue):
                issue_key, result = future.result()
                if result:
                    worklog_results[issue_key] = result

        for issue in issues:
            issue_key = issue.get("key", "Unknown Issue")
            project_data = issue.get("fields", {}).get(Config.CUSTOM_FIELD_RESEARCH_PROJECT, {})
            project = (
                project_data.get("value", "Unknown Project")
                if isinstance(project_data, dict)
                else str(project_data)
            )
            
            total_time_spent = 0
            if issue_key in worklog_results:
                data_full = worklog_results[issue_key]
                all_worklogs = data_full.get("worklogs", [])
                
                cutoff_date = datetime.now() - timedelta(days=14)
                if cutoff_date.tzinfo is None:
                    from datetime import timezone
                    cutoff_date = cutoff_date.replace(tzinfo=timezone.utc)
                
                for wl in all_worklogs:
                    wl_author_id = wl.get("author", {}).get("accountId", "")
                    wl_started = wl.get("started", "")
                    
                    if wl_author_id == assignee_id and wl_started:
                        try:
                            wl_started_clean = wl_started.replace("Z", "+00:00")
                            wl_date = datetime.fromisoformat(wl_started_clean)
                            if wl_date.tzinfo is None:
                                from datetime import timezone
                                wl_date = wl_date.replace(tzinfo=timezone.utc)
                            
                            if wl_date >= cutoff_date:
                                total_time_spent += wl.get("timeSpentSeconds", 0) / 3600
                        except Exception as date_error:
                            logger.warning(f"[WORKLOGS] Failed to parse worklog date {wl_started}: {date_error}")
            
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


def prepare_treemap_data(worklog_issues, time_spent_by_project):
    """
    Prepare treemap data structure grouped by Research Project.
    Returns a hierarchical structure for treemap visualization.
    """
    if not time_spent_by_project or not worklog_issues:
        return None
    
    # Sort projects by hours descending
    sorted_projects = sorted(time_spent_by_project.items(), key=lambda x: x[1], reverse=True)
    
    # Group worklog issues by project
    project_issues = {}
    for issue in worklog_issues:
        project = issue.get("research_project", "Unknown")
        if project not in project_issues:
            project_issues[project] = []
        project_issues[project].append(issue)
    
    # Build treemap data structure
    treemap_data = {
        "name": "Time Distribution",
        "children": []
    }
    
    for project, hours in sorted_projects:
        issues = project_issues.get(project, [])
        # Sort issues within project by hours descending
        issues_sorted = sorted(issues, key=lambda x: x.get("time_spent_hours", 0), reverse=True)
        
        project_node = {
            "name": project,
            "value": round(hours, 2),
            "hours": round(hours, 2),
            "children": [
                {
                    "name": issue.get("name", issue.get("key", "Unknown")),
                    "key": issue.get("key", ""),
                    "value": issue.get("time_spent_hours", 0),
                    "hours": issue.get("time_spent_hours", 0)
                }
                for issue in issues_sorted
            ]
        }
        treemap_data["children"].append(project_node)
    
    return treemap_data


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
    Uses parallel fetching for better performance.
    """
    jira_instance = jira_instance.strip()
    auth = HTTPBasicAuth(email, api_token)
    headers = {"Accept": "application/json"}
    
    issues = []
    visited_issues = set()
    # Store issues to be processed: {key: link_type}
    to_fetch = {issue_key: "Self"}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        while to_fetch:
            # Prepare futures for the current batch
            current_batch = list(to_fetch.items())
            to_fetch = {}  # Clear for next level links
            
            futures = {}
            for key, link_type in current_batch:
                if key in visited_issues:
                    continue
                visited_issues.add(key)
                
                url = f"https://{jira_instance}/rest/api/3/issue/{key}?expand=renderedFields,worklog"
                futures[executor.submit(_make_request, url, headers=headers, auth=auth)] = (key, link_type)
            
            # Process results as they complete
            for future in as_completed(futures):
                key, link_type = futures[future]
                try:
                    response = future.result()
                    if response.status_code != 200:
                        logger.error(
                            f"Failed to fetch issue {key}, "
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
                        f"Issue {key} Assignee Name -> {assignee_name}, "
                        f"Assignee ID -> {assignee_id}"
                    )
                    
                    worklogs = issue_data["fields"].get("worklog", {}).get("worklogs", [])
                    issue_timespent = sum(
                        wl.get("timeSpentSeconds", 0) / 3600 for wl in worklogs
                    )
                    
                    logger.debug(
                        f"Issue {key} Time Spent -> {round(issue_timespent, 2)} hours"
                    )
                    
                    research_project_field = issue_data["fields"].get(Config.CUSTOM_FIELD_RESEARCH_PROJECT)
                    research_project = (
                        research_project_field.get("value")
                        if isinstance(research_project_field, dict)
                        else "N/A"
                    )
                    
                    logger.debug(
                        f"Issue {key} Research Project -> {research_project}"
                    )
                    
                    issues.append({
                        "key": key,
                        "name": issue_name,
                        "description": issue_description,
                        "assignee_name": assignee_name,
                        "assignee_id": assignee_id,
                        "timespent": round(issue_timespent, 2),
                        "research_project": research_project,
                        "link_type": link_type
                    })
                    
                    # Get linked issues for the next level
                    issue_links = get_issue_links(issue_data)
                    for linked_issue in issue_links:
                        l_key = linked_issue["key"]
                        if l_key not in visited_issues:
                            to_fetch[l_key] = linked_issue["link_type"]
                            
                except Exception as e:
                    logger.error(f"Error processing issue {key}: {e}")
    
    logger.debug(f"Completed issue hierarchy retrieval (Total issues: {len(issues)})")
    return issues


def get_jql_from_filter(filter_id, email, api_token, jira_instance):
    """Get the JQL query from a saved Jira filter by filter ID."""
    jira_instance = jira_instance.strip()
    filter_url = f"https://{jira_instance}/rest/api/3/filter/{filter_id}"
    auth = HTTPBasicAuth(email, api_token)
    headers = {"Accept": "application/json"}
    
    try:
        response = _make_request(filter_url, headers=headers, auth=auth)
        
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


def search_issue_by_filter(filter_id, email, api_token, jira_instance, exclude_issue_key=None):
    """
    Search for issues based on a saved Jira filter.
    Returns tuple of (issue_key, total_issues_count).
    
    Args:
        exclude_issue_key: Optional issue key to exclude from results (for getting next issue)
    """
    jira_instance = jira_instance.strip()
    logger.info(f"[SEARCH] Starting search_issue_by_filter with filter_id={filter_id}, exclude_issue_key={exclude_issue_key}")
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
    
    # Get issues and check count (no pagination)
    # If more than maxResults, show "maxResults+"
    max_results = 1000  # Jira's default max per page
    search_url = f"https://{jira_instance}/rest/api/3/search/jql"
    
    # Fetch multiple issues so we can filter out the excluded one in Python
    # This avoids JQL syntax issues with exclusion
    fetch_count = 100 if exclude_issue_key else 1
    payload = {
        "jql": jql,
        "maxResults": fetch_count,
        "fields": ["key"]
    }
    
    logger.info(f"[SEARCH] Making POST request to search URL: {search_url} with maxResults={fetch_count}")
    
    try:
        response = _make_request(
            search_url,
            method="POST",
            headers=headers,
            auth=auth,
            json=payload
        )
        
        logger.info(f"[SEARCH] POST response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            issues = data.get("issues", [])
            
            logger.info(f"[SEARCH] Found {len(issues)} issues in response")
            
            # Filter out excluded issue if specified
            if exclude_issue_key:
                original_count = len(issues)
                issues = [issue for issue in issues if issue["key"] != exclude_issue_key]
                logger.info(f"[SEARCH] After excluding {exclude_issue_key}: {len(issues)} issues remaining (was {original_count})")
            
            if not issues:
                logger.warning(f"[SEARCH] No issues found after exclusion. Full response: {json.dumps(data)}")
                return (None, 0)
            
            issue_key = issues[0]["key"]
            logger.info(f"[SEARCH] Selected next issue: {issue_key}")
            
            # Check total count by requesting max_results (without exclusion for accurate count)
            check_payload = {
                "jql": jql,
                "maxResults": max_results,
                "fields": ["key"]
            }
            check_response = _make_request(
                search_url,
                method="POST",
                headers=headers,
                auth=auth,
                json=check_payload
            )
            
            if check_response.status_code == 200:
                check_data = check_response.json()
                check_issues = check_data.get("issues", [])
                check_is_last = check_data.get("isLast", True)
                
                # If we excluded an issue, subtract 1 from the count
                if exclude_issue_key:
                    excluded_in_results = any(issue["key"] == exclude_issue_key for issue in check_issues)
                    if excluded_in_results:
                        # The excluded issue is in the results, so we need to subtract 1
                        # But only if we're counting exactly, not if it's "max_results+"
                        if check_is_last:
                            total_issues = max(0, len(check_issues) - 1)
                        else:
                            total_issues = f"{max_results}+"
                    else:
                        # Excluded issue not in results (maybe it was already updated and no longer matches filter)
                        if check_is_last:
                            total_issues = len(check_issues)
                        else:
                            total_issues = f"{max_results}+"
                else:
                    if not check_is_last:
                        # More than max_results issues
                        total_issues = f"{max_results}+"
                        logger.info(f"[SEARCH] More than {max_results} issues found, returning '{total_issues}'")
                    else:
                        # Exact count (up to max_results)
                        total_issues = len(check_issues)
                        logger.info(f"[SEARCH] Found exactly {total_issues} issues")
            else:
                # Fallback: if we can't check, use the count from the first request
                if exclude_issue_key:
                    total_issues = len(issues)  # Already filtered
                else:
                    total_issues = len(issues) if issues else 1
                logger.warning(f"[SEARCH] Could not check total, using {total_issues}")
            
            logger.info(f"[SEARCH] Returning issue_key={issue_key}, total_issues={total_issues}")
            return (issue_key, total_issues)
        
        logger.error(
            f"[SEARCH] Error searching issues: {response.status_code}, {response.text}"
        )
        # Try to parse error details if available
        try:
            error_data = response.json()
            logger.error(f"[SEARCH] Error details: {json.dumps(error_data)}")
        except:
            pass
        return None, 0
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching issues: {e}")
        return None, 0


def update_issue(issue_key, research_project, chargeable, email, api_token, jira_instance):
    """
    Update a Jira issue with research project and chargeable status.
    Returns tuple of (success: bool, response_data: dict).
    """
    jira_instance = jira_instance.strip()
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
        response = _make_request(url, method="PUT", json=update_data, auth=auth, headers=headers)
        
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
    jira_instance = jira_instance.strip()
    auth = HTTPBasicAuth(email, api_token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    try:
        # First, get the user's accountId
        user_url = f"https://{jira_instance}/rest/api/3/myself"
        user_response = _make_request(user_url, headers=headers, auth=auth)
        
        if user_response.status_code != 200:
            logger.warning(f"Failed to get user info: {user_response.status_code}")
            return
        
        account_id = user_response.json().get("accountId")
        if not account_id:
            logger.warning("Could not get accountId for watcher")
            return
        
        # Add watcher using accountId
        watcher_url = f"https://{jira_instance}/rest/api/3/issue/{issue_key}/watchers"
        watcher_response = _make_request(
            watcher_url,
            method="POST",
            json=account_id,  # Jira API expects accountId as JSON
            auth=auth,
            headers=headers
        )
        
        if watcher_response.status_code not in [204, 400]:
            # 400 if user is already a watcher
            logger.warning(
                f"Failed to add watcher: {watcher_response.status_code} - "
                f"{watcher_response.text}"
            )
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error adding watcher: {e}")


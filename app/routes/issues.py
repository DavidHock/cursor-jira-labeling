"""
Issue management routes for viewing Jira issues API.
"""
from flask import Blueprint, request, session, jsonify
from app.services.session_service import load_session
from app.services.jira_service import (
    get_issue_hierarchy
)
from app.config import Config
import logging

issues_bp = Blueprint("issues", __name__)
logger = logging.getLogger(__name__)


@issues_bp.route("/fetch_issue", methods=["GET"])
def fetch_issue():
    """Fetch and return a Jira issue with its hierarchy and statistics as JSON."""
    if "jira_email" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    
    load_session()
    
    issue_key = request.args.get("issue_key")
    if not issue_key:
        return jsonify({"message": "issue_key parameter is required"}), 400
    
    logger.debug(f"Fetching issue: {issue_key}")
    
    issues_info = get_issue_hierarchy(
        issue_key,
        session["jira_email"],
        session["jira_api_token"],
        session["jira_instance"]
    )
    
    if not issues_info:
        return jsonify({"message": "Issue not found or unauthorized access"}), 404
    
    assignee_name = issues_info[0].get("assignee_name", "Unassigned")
    task_time_spent = issues_info[0].get("timespent", 0)
    
    total_issues_param = request.args.get("total_issues", "1")
    total_issues = int(total_issues_param)
    logger.info(f"[ROUTE] fetch_issue - Received total_issues param: '{total_issues_param}', converted to: {total_issues}")
    
    response_data = {
        "issues": issues_info,
        "total_issues": total_issues,
        "assignee_name": assignee_name,
        "task_time_spent": task_time_spent
    }
    logger.info(f"[ROUTE] fetch_issue - Returning total_issues in response: {total_issues}")
    return jsonify(response_data), 200


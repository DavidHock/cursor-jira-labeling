"""
Update routes for modifying Jira issues.
"""
from flask import Blueprint, request, session, jsonify
from app.services.session_service import load_session
from app.services.jira_service import (
    update_issue,
    search_issue_by_filter,
    add_watcher
)
from app.config import Config
import logging

update_bp = Blueprint("update", __name__)
logger = logging.getLogger(__name__)


@update_bp.route("/update_issue", methods=["POST"])
def update_issue_route():
    """Update a Jira issue with research project and chargeable status."""
    if "jira_email" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    
    load_session()
    
    data = request.get_json()
    issue_key = data.get("issue_key")
    research_project = data.get("research_project")
    chargeable = data.get("chargeable")
    
    if not issue_key or not research_project:
        return jsonify({"message": "Missing required fields."}), 400
    
    logger.debug(
        f"Updating Issue {issue_key}: "
        f"Research Project -> {research_project}, Chargeable -> {chargeable}"
    )
    
    success, response_data = update_issue(
        issue_key,
        research_project,
        chargeable,
        session["jira_email"],
        session["jira_api_token"],
        session["jira_instance"]
    )
    
    if not success:
        return jsonify(response_data), response_data.get("status_code", 500)
    
    # Add current user as watcher
    add_watcher(
        issue_key,
        session["jira_email"],
        session["jira_api_token"],
        session["jira_instance"]
    )
    
    # Get next issue
    filter_id = session.get("filter_id", Config.DEFAULT_FILTER_ID)
    next_issue_key, total_issues = search_issue_by_filter(
        filter_id,
        session["jira_email"],
        session["jira_api_token"],
        session["jira_instance"]
    )
    
    if next_issue_key:
        # Log the update
        with open(Config.UPDATED_ISSUES_LOG, "a") as f:
            f.write(f"Updated Issue: {issue_key}\n")
        
        return jsonify({
            "message": "Issue updated successfully.",
            "next_issue": next_issue_key,
            "total_issues": total_issues
        }), 200
    else:
        return jsonify({
            "message": "Issue updated, but no more issues found.",
            "next_issue": None
        }), 200


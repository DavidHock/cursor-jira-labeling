"""
Issue management routes for viewing and updating Jira issues.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session
from app.services.session_service import load_session
from app.services.jira_service import (
    get_issue_hierarchy,
    get_recent_worklogs,
    generate_pie_chart
)
from app.config import Config
import logging

issues_bp = Blueprint("issues", __name__, url_prefix="/fetch_issue")
logger = logging.getLogger(__name__)


@issues_bp.route("", methods=["GET"])
def fetch_issue():
    """Fetch and display a Jira issue with its hierarchy and statistics."""
    if "jira_email" not in session:
        return redirect(url_for("auth.home"))
    
    load_session()
    
    issue_key = request.args.get("issue_key")
    if not issue_key:
        return redirect(url_for("search.search_issue"))
    
    logger.debug(f"Fetching issue: {issue_key}")
    
    issues_info = get_issue_hierarchy(
        issue_key,
        session["jira_email"],
        session["jira_api_token"],
        session["jira_instance"]
    )
    
    if not issues_info:
        return "Issue not found or unauthorized access.", 404
    
    assignee_id = issues_info[0].get("assignee_id")
    assignee_name = issues_info[0].get("assignee_name", "Unassigned")
    task_time_spent = issues_info[0].get("timespent", 0)
    
    logger.debug(f"Assignee ID: {assignee_id}, Assignee Name: {assignee_name}")
    
    worklog_issues, worklog_data = (
        get_recent_worklogs(
            assignee_id,
            session["jira_email"],
            session["jira_api_token"],
            session["jira_instance"]
        )
        if assignee_id
        else ([], {})
    )
    
    sorted_projects = sorted(worklog_data.items(), key=lambda x: x[1], reverse=True)
    pie_chart = generate_pie_chart(dict(sorted_projects)) if sorted_projects else None
    
    total_issues = request.args.get("total_issues", 1)
    
    # Known projects list
    known_projects = [
        "6G-NETFAB",
        "GREENFIELD",
        "INTENSE",
        "N-DOLLI",
        "QuINSiDa",
        "SASPIT",
        "SUSTAINET",
        "SHINKA",
        "PARTIALLY ASSIGNABLE",
        "NOT ASSIGNABLE"
    ]
    
    return render_template(
        "issues.html",
        issues=issues_info,
        total_issues=total_issues,
        assignee_name=assignee_name,
        task_time_spent=task_time_spent,
        worklog_issues=worklog_issues,
        sorted_projects=sorted_projects,
        projects_without_time=[p for p in known_projects if p not in worklog_data],
        pie_chart=pie_chart
    )


"""
Search routes for finding Jira issues by filter.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session
from app.services.session_service import load_session
from app.services.jira_service import search_issue_by_filter
from app.config import Config
import logging

search_bp = Blueprint("search", __name__, url_prefix="/search_issue")
logger = logging.getLogger(__name__)


@search_bp.route("", methods=["GET", "POST"])
def search_issue():
    """Search for Jira issues using a filter ID."""
    if "jira_email" not in session:
        return redirect(url_for("auth.home"))
    
    load_session()
    
    if request.method == "POST":
        filter_id = request.form.get("filter_id", Config.DEFAULT_FILTER_ID)
        session["filter_id"] = filter_id
        
        issue_key, total_issues = search_issue_by_filter(
            filter_id,
            session["jira_email"],
            session["jira_api_token"],
            session["jira_instance"]
        )
        
        logger.debug(f"Total issues found: {total_issues}")
        
        if issue_key:
            return redirect(
                url_for("issues.fetch_issue", issue_key=issue_key, total_issues=total_issues)
            )
        else:
            return "No issues found for the given filter.", 404
    
    return render_template(
        "search.html",
        filter_id=session.get("filter_id", Config.DEFAULT_FILTER_ID)
    )


"""
Search routes for finding Jira issues by filter API.
"""
from flask import Blueprint, request, session, jsonify
from app.services.session_service import load_session
from app.services.jira_service import search_issue_by_filter
from app.config import Config
import logging
import json

search_bp = Blueprint("search", __name__)
logger = logging.getLogger(__name__)


@search_bp.route("/search_issue", methods=["POST"])
def search_issue():
    """Search for Jira issues using a filter ID."""
    if "jira_email" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    
    load_session()
    
    data = request.get_json()
    filter_id = data.get("filter_id", Config.DEFAULT_FILTER_ID) if data else Config.DEFAULT_FILTER_ID
    session["filter_id"] = filter_id
    
    issue_key, total_issues = search_issue_by_filter(
        filter_id,
        session["jira_email"],
        session["jira_api_token"],
        session["jira_instance"]
    )
    
    logger.info(f"[ROUTE] search_issue - Received issue_key={issue_key}, total_issues={total_issues}")
    
    if issue_key:
        response_data = {
            "issue_key": issue_key,
            "total_issues": total_issues
        }
        logger.info(f"[ROUTE] search_issue - Returning response: {json.dumps(response_data)}")
        return jsonify(response_data), 200
    else:
        return jsonify({
            "message": "No issues found for the given filter.",
            "issue_key": None,
            "total_issues": 0
        }), 404


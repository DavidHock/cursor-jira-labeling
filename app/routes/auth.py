"""
Authentication routes for Jira login API.
"""
from flask import Blueprint, request, session, jsonify
from app.services.session_service import save_session, load_session
from app.config import Config
import logging

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    """Handle user login and store credentials in session."""
    data = request.get_json()
    
    if not data or not data.get("email") or not data.get("api_token"):
        return jsonify({"message": "Email and API token are required"}), 400
    
    session["jira_email"] = data["email"]
    session["jira_api_token"] = data["api_token"]
    session["jira_instance"] = data.get("jira_instance", Config.JIRA_INSTANCE)
    save_session()
    
    logger.debug(f"Session after login: {dict(session)}")
    
    return jsonify({
        "message": "Login successful",
        "jira_instance": session["jira_instance"]
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Handle user logout."""
    session.clear()
    return jsonify({"message": "Logout successful"}), 200


@auth_bp.route("/session", methods=["GET"])
def get_session():
    """Get current session status."""
    load_session()
    if "jira_email" in session:
        return jsonify({
            "authenticated": True,
            "jira_instance": session.get("jira_instance")
        }), 200
    return jsonify({"authenticated": False}), 200


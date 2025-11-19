"""
Authentication routes for Jira login.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session
from app.services.session_service import save_session, load_session
import logging

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


@auth_bp.route("/")
def home():
    """Home page - displays login form."""
    load_session()
    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def login():
    """Handle user login and store credentials in session."""
    session["jira_email"] = request.form["email"]
    session["jira_api_token"] = request.form["api_token"]
    session["jira_instance"] = "infosim.atlassian.net"
    save_session()
    
    logger.debug(f"Session after login: {dict(session)}")
    
    return redirect(url_for("search.search_issue"))


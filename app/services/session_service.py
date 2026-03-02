"""
Session management service for persisting session data to disk.
"""
import json
import os
from flask import session
from app.config import Config
import logging

logger = logging.getLogger(__name__)


def save_session():
    """Save current Flask session to disk, excluding sensitive credentials."""
    try:
        # Exclude sensitive data from disk persistence
        data_to_save = {k: v for k, v in dict(session).items() if k != "jira_api_token"}
        with open(Config.SESSION_FILE, "w") as f:
            json.dump(data_to_save, f)
    except Exception as e:
        logger.error(f"Failed to save session: {e}")


def load_session():
    """Load session data from disk into Flask session if current session is empty."""
    if "jira_email" not in session and os.path.exists(Config.SESSION_FILE):
        try:
            with open(Config.SESSION_FILE, "r") as f:
                data = json.load(f)
                if data:
                    session.update(data)
                    logger.debug("Session loaded from disk.")
        except Exception as e:
            logger.error(f"Failed to load session: {e}")


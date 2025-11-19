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
    """Save current Flask session to disk."""
    try:
        with open(Config.SESSION_FILE, "w") as f:
            json.dump(dict(session), f)
    except Exception as e:
        logger.error(f"Failed to save session: {e}")


def load_session():
    """Load session data from disk into Flask session."""
    if os.path.exists(Config.SESSION_FILE):
        try:
            with open(Config.SESSION_FILE, "r") as f:
                session.update(json.load(f))
        except Exception as e:
            logger.error(f"Failed to load session: {e}")


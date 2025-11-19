"""
Configuration settings for the Jira Flask application.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key-change-in-production")
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour in seconds
    
    # Jira configuration
    JIRA_INSTANCE = os.environ.get("JIRA_INSTANCE", "infosim.atlassian.net")
    
    # File paths
    SESSION_FILE = os.getenv("SESSION_FILE", "/shared/session_data.json")
    LOG_FILE = os.getenv("LOG_FILE", "/shared/app.log")
    UPDATED_ISSUES_LOG = os.getenv("UPDATED_ISSUES_LOG", "/shared/updated_issues.log")
    
    # Jira custom field IDs
    CUSTOM_FIELD_RESEARCH_PROJECT = "customfield_10097"
    CUSTOM_FIELD_CHARGEABLE = "customfield_10384"
    
    # Default filter ID
    DEFAULT_FILTER_ID = "10456"
    
    # SSL certificates (for local development)
    SSL_CERT = os.getenv("SSL_CERT", "localhost.pem")
    SSL_KEY = os.getenv("SSL_KEY", "localhost-key.pem")
    
    # Flask settings
    HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT = int(os.getenv("FLASK_PORT", "8081"))
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"


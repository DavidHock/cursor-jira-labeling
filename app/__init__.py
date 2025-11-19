"""
Jira Flask Application

A Flask-based web application for managing and analyzing Jira issues.
"""
from flask import Flask
from app.config import Config
from app.routes.auth import auth_bp
from app.routes.issues import issues_bp
from app.routes.search import search_bp
from app.routes.update import update_bp
import logging
import os


def create_app(config_class=Config):
    """Application factory pattern for creating Flask app instances."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure logging
    log_file = os.getenv("LOG_FILE", "/shared/app.log")
    logging.basicConfig(
        level=logging.DEBUG,
        filename=log_file,
        filemode="a",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(issues_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(update_bp)
    
    return app


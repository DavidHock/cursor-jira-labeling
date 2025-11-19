#!/usr/bin/env python3
"""
Main entry point for the Jira Flask application.
"""
from app import create_app
from app.config import Config

app = create_app(Config)

if __name__ == "__main__":
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        ssl_context=(Config.SSL_CERT, Config.SSL_KEY) if Config.SSL_CERT and Config.SSL_KEY else None,
        debug=Config.DEBUG
    )


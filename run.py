#!/usr/bin/env python3
"""
Main entry point for the Jira Flask application.
"""
from app import create_app
from app.config import Config

app = create_app(Config)

if __name__ == "__main__":
    # Only use SSL if certificates exist
    ssl_context = None
    if Config.SSL_CERT and Config.SSL_KEY:
        import os
        if os.path.exists(Config.SSL_CERT) and os.path.exists(Config.SSL_KEY):
            ssl_context = (Config.SSL_CERT, Config.SSL_KEY)
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        ssl_context=ssl_context,
        debug=Config.DEBUG
    )


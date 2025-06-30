"""
Simplified entry point for the Teams Digital Agent
This file can be used for deployment scenarios where you need a clean entry point
"""

import os
import logging
from teams_bot import create_app
from config import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the application"""
    try:
        # Validate configuration
        Config.validate()
        
        # Create the application
        app = create_app()
        
        logger.info(f"Starting Teams Digital Agent on {Config.HOST}:{Config.PORT}")
        
        # Import web runner
        from aiohttp import web
        
        # Run the application
        web.run_app(
            app, 
            host=Config.HOST, 
            port=Config.PORT
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

if __name__ == "__main__":
    main() 
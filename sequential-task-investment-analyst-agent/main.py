"""
Application entry point.
Run with: python main.py
Or with uvicorn: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
import sys

import uvicorn

from config.settings import app_cfg

logging.basicConfig(
    level=getattr(logging, app_cfg.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

# Import the FastAPI app (triggers lifespan on startup)
from src.api.server import app  # noqa: E402

if __name__ == "__main__":
    logger.info("Starting Sequential Task Investment Analyst Agent API")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=app_cfg.debug,
        log_level=app_cfg.log_level.lower(),
    )

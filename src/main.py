#!/usr/bin/env python3
"""Main entry point for ghAuto."""
import asyncio
import logging
import os

import yaml

from db import init_db
from scheduler import AnalysisScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load configuration from file."""
    config_path = os.getenv("GHAUTO_CONFIG", "config.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)


def main():
    """Run ghAuto."""
    config = load_config()

    # Initialize database
    init_db()

    # Get GitHub token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.error("GITHUB_TOKEN environment variable not set")
        return

    # Create scheduler
    scheduler = AnalysisScheduler(
        github_token=token,
        db_path=config.get("database", {}).get("path", "data/ghauto.db"),
    )

    # Run analysis once for the configured user
    # In production, this would be configured per installation
    username = os.getenv("GITHUB_USERNAME")
    if not username:
        logger.error("GITHUB_USERNAME environment variable not set")
        return

    logger.info(f"Running initial analysis for {username}")
    scheduler.run_once(username)

    # Start periodic scheduler
    interval = config.get("github", {}).get("check_interval_hours", 24)
    scheduler.start(username, interval_hours=interval)

    logger.info("ghAuto is running. Press Ctrl+C to stop.")

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        scheduler.stop()


if __name__ == "__main__":
    main()
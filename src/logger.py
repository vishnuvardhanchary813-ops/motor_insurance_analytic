"""Logging utilities for the motor insurance project."""

import logging
from pathlib import Path


def setup_logger():
    """Create and return a logger that writes to logs/pipeline.log."""
    project_dir = Path(__file__).resolve().parent.parent
    log_dir = project_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("motor_insurance_pipeline")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler(
            log_dir / "pipeline.log",
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_pipeline_step(message):
    """Write a pipeline progress message to the log."""
    setup_logger().info(message)


def log_error(message):
    """Write an error message to the log."""
    setup_logger().error(message)
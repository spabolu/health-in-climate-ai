"""
Structured Logging Utilities
=============================

Provides structured logging configuration for the HeatGuard system.
"""

import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from ..config.settings import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry, ensure_ascii=False)


class HeatGuardLogger:
    """Custom logger class for HeatGuard system."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name

    def info(self, message: str, **kwargs):
        """Log info message with optional extra fields."""
        if kwargs:
            extra = {'extra_fields': kwargs}
            self.logger.info(message, extra=extra)
        else:
            self.logger.info(message)

    def warning(self, message: str, **kwargs):
        """Log warning message with optional extra fields."""
        if kwargs:
            extra = {'extra_fields': kwargs}
            self.logger.warning(message, extra=extra)
        else:
            self.logger.warning(message)

    def error(self, message: str, **kwargs):
        """Log error message with optional extra fields."""
        if kwargs:
            extra = {'extra_fields': kwargs}
            self.logger.error(message, extra=extra)
        else:
            self.logger.error(message)

    def debug(self, message: str, **kwargs):
        """Log debug message with optional extra fields."""
        if kwargs:
            extra = {'extra_fields': kwargs}
            self.logger.debug(message, extra=extra)
        else:
            self.logger.debug(message)

    def critical(self, message: str, **kwargs):
        """Log critical message with optional extra fields."""
        if kwargs:
            extra = {'extra_fields': kwargs}
            self.logger.critical(message, extra=extra)
        else:
            self.logger.critical(message)


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    json_format: bool = False
) -> None:
    """
    Setup logging configuration for the HeatGuard system.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (logs to console only if None)
        json_format: Whether to use JSON formatting
    """
    log_level = log_level or settings.LOG_LEVEL
    log_file = log_file or settings.LOG_FILE

    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Setup formatters
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            settings.LOG_FORMAT,
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(file_handler)

    # Setup OSHA compliance logging
    if settings.ENABLE_OSHA_LOGGING:
        setup_osha_logging()

    logging.info(f"Logging configured - Level: {log_level}, File: {log_file or 'Console only'}")


def setup_osha_logging() -> None:
    """Setup OSHA compliance logging."""
    osha_log_path = Path(settings.OSHA_LOG_FILE)
    osha_log_path.parent.mkdir(parents=True, exist_ok=True)

    osha_logger = logging.getLogger('osha_compliance')
    osha_logger.setLevel(logging.INFO)

    # Create OSHA-specific formatter
    osha_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S UTC'
    )

    # OSHA file handler
    osha_handler = logging.handlers.RotatingFileHandler(
        settings.OSHA_LOG_FILE,
        maxBytes=50*1024*1024,  # 50MB
        backupCount=12  # Keep 1 year of monthly logs
    )
    osha_handler.setFormatter(osha_formatter)
    osha_logger.addHandler(osha_handler)

    # Prevent propagation to root logger
    osha_logger.propagate = False


def get_logger(name: str) -> HeatGuardLogger:
    """
    Get a logger instance for the specified module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        HeatGuardLogger instance
    """
    return HeatGuardLogger(name)


def log_prediction(
    worker_id: str,
    risk_score: float,
    risk_level: str,
    temperature: float,
    humidity: float,
    heat_index: float,
    recommendations: list
) -> None:
    """
    Log heat exposure prediction for OSHA compliance.

    Args:
        worker_id: Worker identifier
        risk_score: Heat exposure risk score
        risk_level: Risk assessment level
        temperature: Temperature in Celsius
        humidity: Humidity percentage
        heat_index: Calculated heat index
        recommendations: List of safety recommendations
    """
    osha_logger = logging.getLogger('osha_compliance')

    log_entry = {
        'event_type': 'HEAT_EXPOSURE_PREDICTION',
        'worker_id': worker_id,
        'risk_score': risk_score,
        'risk_level': risk_level,
        'temperature_celsius': temperature,
        'humidity_percent': humidity,
        'heat_index_fahrenheit': heat_index,
        'recommendations_count': len(recommendations),
        'requires_attention': risk_score > 0.75,
        'timestamp_utc': datetime.utcnow().isoformat() + 'Z'
    }

    osha_logger.info(json.dumps(log_entry))


def log_system_event(
    event_type: str,
    message: str,
    **kwargs
) -> None:
    """
    Log system events with structured data.

    Args:
        event_type: Type of system event
        message: Event message
        **kwargs: Additional event data
    """
    system_logger = get_logger('system')

    event_data = {
        'event_type': event_type,
        'message': message,
        **kwargs
    }

    system_logger.info(message, **event_data)


def log_api_request(
    endpoint: str,
    method: str,
    status_code: int,
    response_time: float,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> None:
    """
    Log API request details.

    Args:
        endpoint: API endpoint path
        method: HTTP method
        status_code: HTTP status code
        response_time: Response time in seconds
        user_id: User identifier
        request_id: Request identifier
    """
    api_logger = get_logger('api')

    api_data = {
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'response_time_ms': round(response_time * 1000, 2),
        'user_id': user_id,
        'request_id': request_id
    }

    level = 'error' if status_code >= 400 else 'info'
    message = f"{method} {endpoint} - {status_code} ({response_time*1000:.1f}ms)"

    if level == 'error':
        api_logger.error(message, **api_data)
    else:
        api_logger.info(message, **api_data)


# Initialize logging on module import
if not logging.getLogger().handlers:
    setup_logging()
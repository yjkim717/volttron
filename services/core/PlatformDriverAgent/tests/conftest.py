# -*- coding: utf-8 -*-
"""
conftest.py - Pytest configuration and custom logging for Home Assistant integration tests

This module provides pytest configuration hooks and custom logging functionality
for Home Assistant integration tests. It implements:

1. Custom Logging System:
   - ColoredFormatter: Provides colored console output for better readability
   - PlainFormatter: Provides clean text format for log files
   - Dual logging: Separate handlers for console (colored) and file (plain text)
   - Date-based log file naming: Creates log files named pytest_YYYY-MM-DD.log

2. Feature-based Test Tracking:
   - Automatically categorizes tests by feature type (LIGHT, LOCK, FAN, etc.)
   - Tracks test execution status (passed, failed, skipped) per feature
   - Generates feature-based test summaries at the end of test sessions

3. Pytest Hooks:
   - pytest_configure: Configures pytest logging settings
   - pytest_runtest_logstart: Logs when each test starts
   - pytest_runtest_logreport: Logs test results (pass/fail/skip)
   - pytest_sessionstart: Logs session start
   - pytest_sessionfinish: Generates final test summary report

This module demonstrates the Single Responsibility Principle (SRP) by separating
logging concerns from test logic, and the Open/Closed Principle (OCP) by providing
extensible hooks for custom test reporting.
"""

import logging
import os
import pytest
import sys
from datetime import datetime
from pathlib import Path

CONFTEST_DIR = Path(__file__).parent
LOG_DIR = CONFTEST_DIR.parent / "tests_logs"
os.makedirs(LOG_DIR, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = LOG_DIR / f"pytest_{today}.log"


class ColoredFormatter(logging.Formatter):
    """
    Custom logging formatter that adds ANSI color codes for console output.
    
    This class demonstrates the Single Responsibility Principle (SRP) by
    focusing solely on formatting log messages with colors for terminal display.
    It extends the standard Formatter class, following the Open/Closed
    Principle (OCP).
    
    Colors are applied based on log level:
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Magenta
    """
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record):
        """
        Format log record with ANSI color codes for terminal display.
        
        Args:
            record (logging.LogRecord): The log record to format
            
        Returns:
            str: Formatted log message with color codes
        """
        level = record.levelname
        color = self.COLORS.get(level, '')
        reset = self.RESET
        bold = self.BOLD
        
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        level_str = f"{bold}{color}[{level:8s}]{reset}"
        msg = f"{timestamp} {level_str} {record.getMessage()}"
        
        return msg


class PlainFormatter(logging.Formatter):
    """
    Plain logging formatter without color codes for file output.
    
    This class demonstrates the Single Responsibility Principle (SRP) by
    focusing solely on formatting log messages in plain text format suitable
    for file storage. It extends the standard Formatter class, following
    the Open/Closed Principle (OCP).
    """
    
    def format(self, record):
        """
        Format log record as plain text without color codes.
        
        Args:
            record (logging.LogRecord): The log record to format
            
        Returns:
            str: Formatted log message without color codes
        """
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        level_str = f"[{record.levelname:8s}]"
        msg = f"{timestamp} {level_str} {record.getMessage()}"
        
        return msg


logger = logging.getLogger("HA_TEST_LOGGER")
logger.setLevel(logging.INFO)
logger.handlers.clear()

file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(PlainFormatter())

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(ColoredFormatter())

logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info(f"{'='*80}")
logger.info(f"Test session started - Logging to: {LOG_FILE}")
logger.info(f"{'='*80}")


def get_feature_name(nodeid: str) -> str:
    """
    Determine the feature name from a pytest node ID.
    
    This function demonstrates the Single Responsibility Principle (SRP) by
    having a single purpose: extracting feature type from test node identifiers.
    It uses a simple string matching strategy to categorize tests.
    
    Args:
        nodeid (str): The pytest test node ID (e.g., "test_home_assistant.py::test_light_get_state")
        
    Returns:
        str: The feature name (CLIMATE, LIGHT, LOCK, FAN, SIREN, BOOLEAN, or GENERAL)
        
    Example:
        >>> get_feature_name("test_home_assistant.py::test_light_get_state")
        'LIGHT'
        >>> get_feature_name("test_home_assistant.py::test_climate_set_temperature")
        'CLIMATE'
    """
    nodeid_lower = nodeid.lower()

    if "climate" in nodeid_lower:
        return "CLIMATE"
    elif "light" in nodeid_lower:
        return "LIGHT"
    elif "lock" in nodeid_lower:
        return "LOCK"
    elif "fan" in nodeid_lower:
        return "FAN"
    elif "siren" in nodeid_lower:
        return "SIREN"
    elif "boolean" in nodeid_lower:
        return "BOOLEAN"
    else:
        return "GENERAL"


def pytest_configure(config):
    """
    Pytest configuration hook called after command line options have been parsed.
    
    This hook configures pytest's logging behavior to write logs to a file
    while suppressing default console output. It demonstrates the Open/Closed
    Principle (OCP) by extending pytest's functionality without modifying
    the framework itself.
    
    Args:
        config: The pytest configuration object
    """
    config.option.log_cli = False
    config.option.log_cli_level = "INFO"
    
    log_file = str(LOG_FILE)
    config.option.log_file = log_file
    config.option.log_file_level = "INFO"
    
    logger.debug("Pytest logging configured")


_feature_tracker = {}


def _track_feature_start(feature: str, nodeid: str):
    """
    Track when a feature's first test starts and log the feature header.
    
    This function demonstrates the Single Responsibility Principle (SRP) by
    handling only the tracking of feature test starts. It maintains state in
    the module-level _feature_tracker dictionary.
    
    Args:
        feature (str): The feature name (e.g., "LIGHT", "CLIMATE")
        nodeid (str): The pytest test node ID
    """
    if feature not in _feature_tracker:
        _feature_tracker[feature] = {
            'started': True,
            'tests': [],
            'passed': 0,
            'failed': 0,
            'skipped': 0
        }
        logger.info(f"\n{'─'*80}")
        logger.info(f"[{feature}] Feature Test Started")
        logger.info(f"{'─'*80}")
    _feature_tracker[feature]['tests'].append(nodeid)


def _track_feature_result(feature: str, nodeid: str, status: str):
    """
    Track test results and update feature statistics.
    
    This function demonstrates the Single Responsibility Principle (SRP) by
    handling only the tracking of test results. It updates the feature
    statistics in the _feature_tracker dictionary.
    
    Args:
        feature (str): The feature name (e.g., "LIGHT", "CLIMATE")
        nodeid (str): The pytest test node ID
        status (str): The test status ("passed", "failed", or "skipped")
    """
    if feature in _feature_tracker:
        if status == 'passed':
            _feature_tracker[feature]['passed'] += 1
        elif status == 'failed':
            _feature_tracker[feature]['failed'] += 1
        elif status == 'skipped':
            _feature_tracker[feature]['skipped'] += 1


def pytest_runtest_logstart(nodeid, location):
    """
    Pytest hook called when a test starts running.
    
    This hook logs the start of each test with its feature category and
    location information. It demonstrates the Open/Closed Principle (OCP)
    by extending pytest's reporting without modifying the framework.
    
    Args:
        nodeid: The pytest test node ID
        location: Tuple of (file_path, line_number, function_name)
    """
    feature = get_feature_name(nodeid)
    _track_feature_start(feature, nodeid)
    file_path, line_num, func_name = location
    logger.info(f"  [{feature}] START: {func_name} (Line {line_num})")


def pytest_runtest_logreport(report):
    """
    Pytest hook called when a test report is ready.
    
    This hook processes test results and logs them with appropriate formatting.
    It handles three phases: setup, call (actual test execution), and teardown.
    It demonstrates the Single Responsibility Principle (SRP) by handling
    only test result logging and tracking.
    
    Args:
        report: The pytest test report object containing test results
    """
    if report.when == "call":
        feature = get_feature_name(report.nodeid)
        duration = getattr(report, 'duration', 0)

        if report.passed:
            logger.info(f"  [{feature}] PASS: {report.nodeid.split('::')[-1]} ({duration:.3f}s)")
            _track_feature_result(feature, report.nodeid, 'passed')
        elif report.failed:
            error_msg = report.longreprtext if hasattr(report, 'longreprtext') else str(report.longrepr)
            logger.error(f"  [{feature}] FAIL: {report.nodeid.split('::')[-1]} ({duration:.3f}s)")
            logger.error(f"  [{feature}] Error: {error_msg[:200]}..." if len(error_msg) > 200 else f"  [{feature}] Error: {error_msg}")
            _track_feature_result(feature, report.nodeid, 'failed')
        elif report.skipped:
            skip_reason = getattr(report, 'longrepr', 'No reason provided')
            logger.warning(f"  [{feature}] SKIPPED: {report.nodeid.split('::')[-1]} - {skip_reason}")
            _track_feature_result(feature, report.nodeid, 'skipped')
    elif report.when == "setup":
        feature = get_feature_name(report.nodeid)
        if report.failed:
            logger.error(f"  [{feature}] SETUP FAILED: {report.nodeid}")
            logger.error(f"  [{feature}] Error: {report.longreprtext[:200]}..." if len(report.longreprtext) > 200 else f"  [{feature}] Error: {report.longreprtext}")
    elif report.when == "teardown":
        feature = get_feature_name(report.nodeid)
        if report.failed:
            logger.error(f"  [{feature}] TEARDOWN FAILED: {report.nodeid}")
            logger.error(f"  [{feature}] Error: {report.longreprtext[:200]}..." if len(report.longreprtext) > 200 else f"  [{feature}] Error: {report.longreprtext}")


def pytest_sessionstart(session):
    """
    Pytest hook called when the test session starts.
    
    This hook logs the start of the test session. It demonstrates the
    Open/Closed Principle (OCP) by extending pytest's session lifecycle
    without modifying the framework.
    
    Args:
        session: The pytest session object
    """
    logger.info("Pytest session started")


def pytest_sessionfinish(session, exitstatus):
    """
    Pytest hook called when the test session finishes.
    
    This hook generates a comprehensive test summary report organized by
    feature. It demonstrates the Single Responsibility Principle (SRP) by
    handling only the final summary generation and logging.
    
    The summary includes:
    - Per-feature test statistics (passed/failed/skipped)
    - Overall test statistics
    - List of failed tests (if any)
    
    Args:
        session: The pytest session object
        exitstatus: The exit status code (0 for success, non-zero for failure)
    """
    logger.info(f"\n{'═'*80}")
    logger.info("Pytest session finished")
    logger.info(f"{'═'*80}")
    
    if _feature_tracker:
        logger.info("\nFeature Test Summary")
        logger.info(f"{'─'*80}")
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        
        for feature in sorted(_feature_tracker.keys()):
            tracker = _feature_tracker[feature]
            total = tracker['passed'] + tracker['failed'] + tracker['skipped']
            total_passed += tracker['passed']
            total_failed += tracker['failed']
            total_skipped += tracker['skipped']
            
            if tracker['failed'] == 0:
                logger.info(f"  [{feature}] PASSED: {tracker['passed']}/{total} tests passed" + 
                          (f", {tracker['skipped']} skipped" if tracker['skipped'] > 0 else ""))
            else:
                logger.error(f"  [{feature}] FAILED: {tracker['failed']} failed, {tracker['passed']} passed" + 
                           (f", {tracker['skipped']} skipped" if tracker['skipped'] > 0 else ""))
                for test_nodeid in tracker['tests']:
                    test_name = test_nodeid.split('::')[-1]
                    logger.error(f"      - {test_name}")
        
        logger.info(f"{'─'*80}")
        status_text = "PASSED" if total_failed == 0 else "FAILED"
        logger.info(f"  Overall: {total_passed} passed, {total_failed} failed, {total_skipped} skipped ({status_text})")
        logger.info(f"{'═'*80}")
    
    logger.info(f"\nLog file: {LOG_FILE}")
    logger.info(f"Exit status: {exitstatus}\n")

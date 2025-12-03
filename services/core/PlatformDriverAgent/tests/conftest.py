# conftest.py
import logging
import os
import pytest
import sys
from datetime import datetime
from pathlib import Path

# ------------------------------------------------------------
# Create log folder (using absolute path based on conftest.py location)
# ------------------------------------------------------------
CONFTEST_DIR = Path(__file__).parent
LOG_DIR = CONFTEST_DIR.parent / "tests_logs"
os.makedirs(LOG_DIR, exist_ok=True)

# ------------------------------------------------------------
# Create date-based log filename
# ------------------------------------------------------------
today = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = LOG_DIR / f"pytest_{today}.log"

# ------------------------------------------------------------
# Custom formatters: one with colors (console), one without (file)
# ------------------------------------------------------------
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console"""
    
    # ANSI color codes
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
        # Get color for this log level
        level = record.levelname
        color = self.COLORS.get(level, '')
        reset = self.RESET
        bold = self.BOLD
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format with colors (for console)
        level_str = f"{bold}{color}[{level:8s}]{reset}"
        msg = f"{timestamp} {level_str} {record.getMessage()}"
        
        return msg


class PlainFormatter(logging.Formatter):
    """Plain formatter without colors for log file"""
    
    def format(self, record):
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format without colors (for file)
        level_str = f"[{record.levelname:8s}]"
        msg = f"{timestamp} {level_str} {record.getMessage()}"
        
        return msg


# ------------------------------------------------------------
# Configure Python logging with separate formatters
# ------------------------------------------------------------
logger = logging.getLogger("HA_TEST_LOGGER")
logger.setLevel(logging.INFO)
logger.handlers.clear()  # Clear any existing handlers

# File handler: NO colors (clean text format)
file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(PlainFormatter())

# Console handler: WITH colors (for terminal viewing)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(ColoredFormatter())

logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info(f"{'='*80}")
logger.info(f"Test session started - Logging to: {LOG_FILE}")
logger.info(f"{'='*80}")

# ------------------------------------------------------------
# Determine feature type from node ID
# ------------------------------------------------------------
def get_feature_name(nodeid: str) -> str:
    nodeid_lower = nodeid.lower()

    if "climate" in nodeid_lower:
        return "CLIMATE"
    elif "light" in nodeid_lower:
        return "LIGHT"
    elif "lock" in nodeid_lower:
        return "LOCK"
    elif "fan" in nodeid_lower:
        return "FAN"
    elif "boolean" in nodeid_lower:
        return "BOOLEAN"
    else:
        return "GENERAL"

# ------------------------------------------------------------
# Pytest Configuration Hook
# ------------------------------------------------------------
def pytest_configure(config):
    """Configure pytest logging to write to file"""
    # Set log level
    config.option.log_cli = False  # Don't show logs in console by default
    config.option.log_cli_level = "INFO"
    
    # Configure logging to file
    log_file = str(LOG_FILE)
    config.option.log_file = log_file
    config.option.log_file_level = "INFO"
    
    logger.debug("Pytest logging configured")

# ------------------------------------------------------------
# Track feature test status
# ------------------------------------------------------------
_feature_tracker = {}  # {feature_name: {'started': bool, 'tests': list, 'passed': int, 'failed': int}}

def _track_feature_start(feature: str, nodeid: str):
    """Track when a feature's first test starts"""
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
    """Track test results and log feature completion"""
    if feature in _feature_tracker:
        if status == 'passed':
            _feature_tracker[feature]['passed'] += 1
        elif status == 'failed':
            _feature_tracker[feature]['failed'] += 1
        elif status == 'skipped':
            _feature_tracker[feature]['skipped'] += 1

# ------------------------------------------------------------
# Pytest Hooks
# ------------------------------------------------------------
def pytest_runtest_logstart(nodeid, location):
    feature = get_feature_name(nodeid)
    _track_feature_start(feature, nodeid)
    file_path, line_num, func_name = location
    logger.info(f"  [{feature}] START: {func_name} (Line {line_num})")

def pytest_runtest_logreport(report):
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
    """Called after the Session object has been created"""
    logger.info("Pytest session started")

def pytest_sessionfinish(session, exitstatus):
    logger.info(f"\n{'═'*80}")
    logger.info("Pytest session finished")
    logger.info(f"{'═'*80}")
    
    # Log feature test summaries
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
                # Log failed test names
                for test_nodeid in tracker['tests']:
                    test_name = test_nodeid.split('::')[-1]
                    logger.error(f"      - {test_name}")
        
        logger.info(f"{'─'*80}")
        status_text = "PASSED" if total_failed == 0 else "FAILED"
        logger.info(f"  Overall: {total_passed} passed, {total_failed} failed, {total_skipped} skipped ({status_text})")
        logger.info(f"{'═'*80}")
    
    logger.info(f"\nLog file: {LOG_FILE}")
    logger.info(f"Exit status: {exitstatus}\n")

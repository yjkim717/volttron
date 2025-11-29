# conftest.py
import logging
import os
import pytest
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
# Configure Python logging
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),  # 'a' for append
        logging.StreamHandler()
    ],
    force=True  # Override any existing configuration
)

logger = logging.getLogger("HA_TEST_LOGGER")
logger.info(f"=== Test session started - Logging to: {LOG_FILE} ===")

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
    
    logger.info("Pytest logging configured")

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
        logger.info(f"[{feature}] ===== {feature} Feature Test Started =====")
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
    logger.info(f"[{feature}] START: {nodeid} (File: {file_path}, Line: {line_num}, Function: {func_name})")

def pytest_runtest_logreport(report):
    if report.when == "call":
        feature = get_feature_name(report.nodeid)
        duration = getattr(report, 'duration', 0)

        if report.passed:
            logger.info(f"[{feature}] PASS: {report.nodeid} (Duration: {duration:.3f}s)")
            _track_feature_result(feature, report.nodeid, 'passed')
        elif report.failed:
            error_msg = report.longreprtext if hasattr(report, 'longreprtext') else str(report.longrepr)
            logger.error(f"[{feature}] FAIL: {report.nodeid} (Duration: {duration:.3f}s)")
            logger.error(f"[{feature}] Error Details: {error_msg}")
            _track_feature_result(feature, report.nodeid, 'failed')
        elif report.skipped:
            skip_reason = getattr(report, 'longrepr', 'No reason provided')
            logger.warning(f"[{feature}] SKIPPED: {report.nodeid} - Reason: {skip_reason}")
            _track_feature_result(feature, report.nodeid, 'skipped')
    elif report.when == "setup":
        feature = get_feature_name(report.nodeid)
        if report.failed:
            logger.error(f"[{feature}] SETUP FAILED: {report.nodeid} - {report.longreprtext}")
    elif report.when == "teardown":
        feature = get_feature_name(report.nodeid)
        if report.failed:
            logger.error(f"[{feature}] TEARDOWN FAILED: {report.nodeid} - {report.longreprtext}")

def pytest_sessionstart(session):
    """Called after the Session object has been created"""
    logger.info("=== Pytest session started ===")

def pytest_sessionfinish(session, exitstatus):
    logger.info("=== Pytest session finished ===")
    
    # Log feature test summaries
    if _feature_tracker:
        logger.info("--- Feature Test Summary ---")
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
                logger.info(f"[{feature}] ===== {feature} Feature Test PASSED ({tracker['passed']}/{total} tests passed, {tracker['skipped']} skipped) =====")
            else:
                logger.error(f"[{feature}] ===== {feature} Feature Test FAILED ({tracker['failed']} failed, {tracker['passed']} passed, {tracker['skipped']} skipped) =====")
                # Log failed test names
                for test_nodeid in tracker['tests']:
                    logger.error(f"[{feature}] Failed test: {test_nodeid}")
        
        logger.info(f"--- Overall Summary: {total_passed} passed, {total_failed} failed, {total_skipped} skipped ---")
    
    logger.info(f"Exit status: {exitstatus}")
    logger.info(f"Log file saved to: {LOG_FILE}")

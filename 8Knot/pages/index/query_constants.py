"""
Constants for query job management and priority loading.

Centralizes all magic strings, timeouts, and configuration values
to follow DRY and maintainability best practices.
"""

# ============================================================================
# QUERY JOB STATUS CONSTANTS
# ============================================================================

QUERY_STATUS_CACHED = "cached"
QUERY_STATUS_PENDING = "pending"

# ============================================================================
# PAGE LOADING STATUS CONSTANTS
# ============================================================================

PAGE_STATUS_IDLE = "idle"
PAGE_STATUS_READY = "ready"
PAGE_STATUS_FAILED = "failed"
PAGE_STATUS_TIMEOUT = "timeout"

# ============================================================================
# POLLING AND TIMEOUT CONFIGURATION
# ============================================================================

# How often to poll job status
GLOBAL_QUERY_POLL_INTERVAL = 2.0  # seconds - slow polling for all background queries
CURRENT_PAGE_POLL_INTERVAL = 0.5  # seconds - fast polling for current page queries
FAILURE_WAIT_INTERVAL = 4.0  # seconds - wait between failure state checks

# Maximum time to wait for queries
MAX_QUERY_WAIT_TIME = 600  # seconds - 10 minute timeout for query completion

# ============================================================================
# DATA BADGE UI CONSTANTS
# ============================================================================

# Badge text messages
BADGE_TEXT_NO_DATA = "No Data"
BADGE_TEXT_ALL_READY = "All Data Ready"
BADGE_TEXT_PAGE_READY = "Page Ready (loading more...)"
BADGE_TEXT_PAGE_FAILED = "Page Load Failed"
BADGE_TEXT_PAGE_TIMEOUT = "Page Timeout"
BADGE_TEXT_DATA_READY = "Data Ready"
BADGE_TEXT_TIMEOUT_RETRY = "Timeout - Retry"
BADGE_TEXT_DATA_INCOMPLETE = "Data Incomplete- Retry"

# Badge colors (Baby Blue color scheme)
BADGE_COLOR_READY = "#0F5880"  # Baby Blue 700 - dark blue for success
BADGE_COLOR_LOADING = "#199AD6"  # Baby Blue 500 - medium blue for in-progress
BADGE_COLOR_ERROR = "danger"  # Bootstrap danger color
BADGE_COLOR_WARNING = "warning"  # Bootstrap warning color
BADGE_COLOR_SECONDARY = "secondary"  # Bootstrap secondary color

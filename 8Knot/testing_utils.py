"""
Testing utilities for 8Knot application.

This module provides utilities to instrument the application for better
error detection during CI/CD testing.
"""

import os
import sys
import logging
import traceback
from functools import wraps

# Configure logging for testing
def setup_testing_logging():
    """Configure logging to be more descriptive during testing."""
    if os.getenv("8KNOT_DEBUG", "False") == "True":
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[logging.StreamHandler(sys.stdout), logging.StreamHandler(sys.stderr)],
        )

        # Set specific loggers
        logging.getLogger("dash").setLevel(logging.DEBUG)
        logging.getLogger("werkzeug").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def fail_fast_on_error(func):
    """
    Decorator that causes the application to exit immediately on errors
    during testing.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if os.getenv("8KNOT_DEBUG", "False") == "True":
                logging.error(f"CRITICAL ERROR in {func.__name__}: {str(e)}")
                logging.error(f"Traceback: {traceback.format_exc()}")

                # In testing mode, exit immediately on critical errors
                if os.getenv("CI", "False") == "True":
                    logging.error("Exiting due to critical error in CI environment")
                    sys.exit(1)
            raise

    return wrapper


def check_required_services():
    """
    Check that all required services are available.
    This function can be called during application startup to ensure
    all dependencies are properly configured.
    """
    checks = []

    # Check environment variables
    required_env_vars = [
        "AUGUR_DATABASE",
        "AUGUR_HOST",
        "AUGUR_PASSWORD",
        "AUGUR_USERNAME",
        "REDIS_PASSWORD",
        "POSTGRES_PASSWORD",
    ]

    for var in required_env_vars:
        if not os.getenv(var):
            checks.append(f"Missing required environment variable: {var}")

    # Check database connectivity (if augur manager is available)
    try:
        from db_manager.augur_manager import AugurManager

        augur = AugurManager()
        engine = augur.get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        checks.append("Database connection: OK")
    except Exception as e:
        checks.append(f"Database connection failed: {str(e)}")

    # Check Redis connectivity
    try:
        import redis

        redis_cache = redis.StrictRedis(
            host=os.getenv("REDIS_SERVICE_CACHE_HOST", "redis-cache"),
            port=6379,
            password=os.getenv("REDIS_PASSWORD", ""),
        )
        redis_cache.ping()
        checks.append("Redis cache connection: OK")
    except Exception as e:
        checks.append(f"Redis cache connection failed: {str(e)}")

    return checks


def log_service_status():
    """Log the status of all required services."""
    logging.info("=== Service Status Check ===")
    checks = check_required_services()
    for check in checks:
        if "failed" in check.lower() or "missing" in check.lower():
            logging.error(check)
        else:
            logging.info(check)
    logging.info("=== End Service Status ===")


def validate_visualization_data(data, visualization_name):
    """
    Validate that visualization data is properly formatted.
    """
    if data is None:
        logging.warning(f"No data available for visualization: {visualization_name}")
        return False

    if hasattr(data, "empty") and data.empty:
        logging.warning(f"Empty dataset for visualization: {visualization_name}")
        return False

    if hasattr(data, "__len__") and len(data) == 0:
        logging.warning(f"Empty data for visualization: {visualization_name}")
        return False

    logging.debug(f"Data validation passed for visualization: {visualization_name}")
    return True


# Initialize testing utilities if in debug mode
if os.getenv("8KNOT_DEBUG", "False") == "True":
    setup_testing_logging()
    logging.info("Testing utilities initialized")


def check_security_vulnerabilities():
    """
    Check for security vulnerabilities in installed packages.
    Used by nightly dependency testing.
    """
    try:
        import subprocess
        import json

        # Run safety check
        result = subprocess.run(["safety", "check", "--json"], capture_output=True, text=True)

        if result.returncode == 0:
            logging.info("No security vulnerabilities found")
            return []
        else:
            # Parse JSON output
            try:
                vulnerabilities = json.loads(result.stdout)
                logging.warning(f"Found {len(vulnerabilities)} security vulnerabilities")
                return vulnerabilities
            except json.JSONDecodeError:
                logging.error("Could not parse safety check output")
                return []

    except ImportError:
        logging.warning("Safety package not installed - skipping security check")
        return []
    except Exception as e:
        logging.error(f"Security check failed: {str(e)}")
        return []


def validate_dependency_compatibility():
    """
    Check if all installed packages are compatible with each other.
    Used by nightly dependency testing.
    """
    try:
        import subprocess

        # Try uv first, fall back to pip
        try:
            result = subprocess.run(["uv", "pip", "check", "--system"], capture_output=True, text=True)
        except FileNotFoundError:
            # Fall back to pip if uv is not available
            result = subprocess.run(["pip", "check"], capture_output=True, text=True)

        if result.returncode == 0:
            logging.info("All dependencies are compatible")
            return True
        else:
            logging.error(f"Dependency conflicts found: {result.stdout}")
            return False

    except Exception as e:
        logging.error(f"Dependency compatibility check failed: {str(e)}")
        return False


def log_package_versions():
    """
    Log the versions of all installed packages.
    Useful for debugging dependency issues.
    """
    try:
        import subprocess

        # Try uv first, fall back to pip
        try:
            result = subprocess.run(["uv", "pip", "list", "--system"], capture_output=True, text=True)
        except FileNotFoundError:
            # Fall back to pip if uv is not available
            result = subprocess.run(["pip", "list"], capture_output=True, text=True)

        if result.returncode == 0:
            logging.info("Installed package versions:")
            for line in result.stdout.split("\n")[:20]:  # Log first 20 packages
                if line.strip():
                    logging.info(f"  {line}")
        else:
            logging.error("Could not retrieve package versions")

    except Exception as e:
        logging.error(f"Package version logging failed: {str(e)}")


def run_nightly_health_checks():
    """
    Run comprehensive health checks for nightly testing.
    Combines all validation functions for thorough testing.
    """
    logging.info("=== Nightly Health Check Started ===")

    # Basic service checks
    service_checks = check_required_services()
    for check in service_checks:
        if "failed" in check.lower() or "missing" in check.lower():
            logging.error(check)
        else:
            logging.info(check)

    # Security vulnerability check
    vulnerabilities = check_security_vulnerabilities()
    if vulnerabilities:
        logging.warning(f"Security vulnerabilities found: {len(vulnerabilities)}")
        for vuln in vulnerabilities[:5]:  # Log first 5 vulnerabilities
            logging.warning(f"  {vuln.get('package', 'Unknown')} - {vuln.get('vulnerability', 'Unknown issue')}")

    # Dependency compatibility check
    deps_compatible = validate_dependency_compatibility()
    if not deps_compatible:
        logging.error("Dependency compatibility issues detected")

    # Log package versions for debugging
    log_package_versions()

    logging.info("=== Nightly Health Check Completed ===")

    return {
        "service_checks": service_checks,
        "vulnerabilities": vulnerabilities,
        "dependencies_compatible": deps_compatible,
    }


# Run nightly health checks if in nightly testing mode
if os.getenv("NIGHTLY_TEST", "False") == "True":
    run_nightly_health_checks()

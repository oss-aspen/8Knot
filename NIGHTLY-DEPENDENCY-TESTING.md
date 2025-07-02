# Nightly Dependency Testing Guide

## 🌙 Overview

8Knot automatically tests dependency updates every night at 2 AM UTC to ensure the application remains compatible with the latest package versions and secure from known vulnerabilities.

## 🔍 What happens during nightly testing?

### 1. Dependency Updates
- **Removes version pins** from `requirements.txt` to get latest versions
- **Uses `uv`** for fast dependency resolution and installation
- **Creates backup** of original requirements for rollback

### 2. Security Scanning
- **Runs `safety` tool** to scan for known CVEs in dependencies
- **Generates security reports** in JSON format
- **Flags vulnerable packages** for immediate attention

### 3. Application Testing
- **Builds Docker Compose stack** with updated dependencies
- **Tests all critical endpoints** to ensure functionality
- **Monitors application logs** for errors or exceptions
- **Verifies database connectivity** through health check endpoint

### 4. Conflict Detection
- **Checks dependency compatibility** using `uv pip check`
- **Identifies version conflicts** between packages
- **Reports resolution issues** for manual review

### 5. Automated Issue Creation
- **Creates GitHub issues** automatically when tests fail
- **Includes detailed error information** and workflow links
- **Attaches debugging artifacts** (security reports, package lists)
- **Prevents duplicate issues** (maximum one per day)

## 🛠️ Tested Endpoints

The nightly test verifies these critical application pages:
- `/` - Welcome page
- `/contributions` - Contribution metrics
- `/contributors/contribution_types` - Contributor type analysis
- `/contributors/behavior` - Contributor behavior patterns
- `/chaoss` - CHAOSS metrics
- `/codebase` - Codebase analysis
- `/affiliation` - Organization affiliation data
- `/info` - Information and definitions
- `/repo_overview` - Repository overview
- `/health` - Health check endpoint

## 🔧 Health Check Endpoint

The application includes a health check endpoint at `/health` that:
- **Tests database connectivity** to ensure Augur database is accessible
- **Returns JSON status** with timestamp and connection status
- **Used by nightly CI** to verify application readiness

Example response:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-15 10:30:00"
}
```

## 🚨 When Things Go Wrong

### Automatic Issue Creation
If the nightly test fails, GitHub automatically creates an issue with:
- **Error details** and links to failed workflow runs
- **Security scan results** if vulnerabilities are found
- **Downloadable artifacts** for debugging:
  - `safety_report.json` - Security vulnerability report
  - `requirements_latest_pinned.txt` - Latest package versions tested
  - `installed_packages.txt` - Full list of installed packages
  - `requirements.txt.backup` - Original requirements backup

### Common Failure Scenarios
1. **Security vulnerabilities** - New CVEs discovered in dependencies
2. **Breaking changes** - Latest package versions break existing functionality
3. **Dependency conflicts** - Packages can't resolve compatible versions
4. **Application errors** - Code incompatible with new package APIs

## 🧪 Testing Locally

To test dependency updates locally before they're automatically tested:

### Using Docker (same as CI):
```bash
# 1. Backup your requirements
cp requirements.txt requirements.txt.backup

# 2. Remove version pins to get latest versions
sed 's/==.*$//' requirements.txt > requirements_latest.txt
mv requirements_latest.txt requirements.txt

# 3. Install uv for fast dependency management
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# 4. Build and test with updated dependencies
docker compose up --build -d

# 5. Wait for services to be ready
timeout 300 bash -c 'until curl -f http://localhost:8080/health; do sleep 5; done'

# 6. Test critical endpoints
curl http://localhost:8080/
curl http://localhost:8080/contributions
curl http://localhost:8080/health

# 7. Run security scan
uv pip install --system safety
safety check

# 8. Check for dependency conflicts
uv pip check --system

# 9. Restore original requirements when done
mv requirements.txt.backup requirements.txt
```

### Using Podman (alternative):
```bash
# Same steps as Docker, but replace 'docker compose' with 'podman compose'
podman compose up --build -d
podman compose logs app-server
```

## 📊 Understanding Results

### ✅ Success (Green):
- All dependencies updated successfully
- No security vulnerabilities found
- All endpoints responding correctly
- No dependency conflicts detected

### ❌ Failure (Red):
- Security vulnerabilities discovered
- Breaking changes in new package versions
- Dependency resolution conflicts
- Application errors with updated packages

### 🔍 Debugging Failures:
1. **Check the GitHub issue** created automatically
2. **Download artifacts** from the failed workflow
3. **Review security report** for vulnerable packages
4. **Test locally** using the steps above
5. **Pin problematic packages** in requirements.txt if needed

## 🔒 Security Features

### Vulnerability Scanning:
- **Daily scans** of all Python dependencies
- **JSON reports** saved as artifacts
- **Immediate alerts** via GitHub issues
- **CVE database** integration through `safety` tool

### Best Practices:
- **Review security issues** promptly when created
- **Update vulnerable packages** as soon as patches available
- **Pin versions** temporarily if updates break functionality
- **Monitor security advisories** for critical dependencies

## 🎯 Benefits

1. **Early Detection** - Find dependency issues before they affect users
2. **Security Monitoring** - Automated vulnerability scanning
3. **Compatibility Testing** - Ensure new versions don't break functionality
4. **Zero Maintenance** - Fully automated with issue creation
5. **Artifact Preservation** - Debug information saved for analysis

## 📅 Schedule

- **Runtime**: Every night at 2:00 AM UTC
- **Duration**: ~30 minutes maximum
- **Timeout**: Automatic failure if tests take longer
- **Manual Trigger**: Available via GitHub Actions interface

The nightly dependency testing ensures 8Knot stays secure and compatible with the evolving Python ecosystem while requiring minimal manual intervention.

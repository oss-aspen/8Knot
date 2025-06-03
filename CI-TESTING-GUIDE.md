# CI Testing Quick Reference

## 🚀 What happens when you create a PR?

1. **Automatic Build**: GitHub Actions automatically builds your Docker Compose stack
2. **Service Health Checks**: Waits for PostgreSQL, Redis, and app server to be ready
3. **Endpoint Testing**: Tests all major visualization pages to ensure they load
4. **Error Detection**: Scans logs for critical errors and reports them
5. **Status Report**: Shows green ✅ or red ❌ status on your PR

## 🔍 What gets tested?

### Pages tested on every PR:
- `/` - Welcome page
- `/contributions` - Contribution metrics
- `/contributors/contribution_types` - Contributor type analysis
- `/contributors/behavior` - Contributor behavior patterns
- `/chaoss` - CHAOSS metrics
- `/codebase` - Codebase analysis
- `/affiliation` - Organization affiliation data
- `/info` - Information and definitions
- `/repo_overview` - Repository overview

### Health checks:
- Database connectivity
- Redis cache availability
- Application server responsiveness
- Service startup order

## 🌙 Nightly Dependency Testing

Every night at 2 AM UTC, the system automatically:
- **Updates all dependencies** to their latest versions
- **Rebuilds and tests** the application with new packages using `uv` for fast installation
- **Runs security vulnerability scans** using `safety` tool
- **Tests all endpoints** to ensure compatibility
- **Creates GitHub issues** automatically if problems are found
- **Saves artifacts** for debugging (security reports, package lists)

### What gets tested nightly:
- **Latest package versions** - Removes version pins from `requirements.txt`
- **Security vulnerabilities** - Scans for known CVEs in dependencies
- **Breaking changes** - Tests if new versions break existing functionality
- **Dependency conflicts** - Checks if packages can resolve together
- **Application stability** - Ensures all endpoints still work

### Automatic issue creation:
If the nightly test fails, it automatically creates a GitHub issue with:
- **Detailed error information** and workflow links
- **Security scan results** if vulnerabilities are found
- **Artifact downloads** for debugging
- **Recommended next steps** for fixing issues
- **Prevents duplicate issues** (one per day maximum)

## 🛠️ For Developers

### Testing locally before PR:

**Option 1: Using Docker (same as CI)**
```bash
# Use the same commands as CI
docker compose up --build -d

# Wait for services
docker compose ps

# Test endpoints manually
curl http://localhost:8080/
curl http://localhost:8080/contributions
curl http://localhost:8080/health

# Check logs
docker compose logs app-server
```

**Option 2: Using Podman (recommended for local development)**
```bash
# Use Podman instead of Docker
podman compose up --build -d

# Wait for services
podman compose ps

# Test endpoints manually (same as Docker)
curl http://localhost:8080/
curl http://localhost:8080/contributions
curl http://localhost:8080/health

# Check logs
podman compose logs app-server
```

> **Note**: CI always uses Docker, but you can use either Docker or Podman locally. Both should produce same results.

### Testing dependency updates locally:
```bash
# Test with latest dependencies (same as nightly CI)
# 1. Backup your requirements
cp requirements.txt requirements.txt.backup

# 2. Remove version pins to get latest
sed 's/==.*$//' requirements.txt > requirements_latest.txt
mv requirements_latest.txt requirements.txt

# 3. Install uv if not already available
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# 4. Test with Docker or Podman
docker compose up --build -d
# OR
podman compose up --build -d

# 5. Run security scan (using uv for faster installation)
uv pip install --system safety
safety check

# 6. Check dependency compatibility
uv pip check --system

# 7. Test all endpoints
curl http://localhost:8080/health
curl http://localhost:8080/contributions
# ... test other endpoints

# 8. Restore original requirements when done
mv requirements.txt.backup requirements.txt
```

> **Note**: The nightly CI uses `uv` instead of `pip` for faster dependency resolution and installation.

### If CI fails:
1. **Check the logs** in the GitHub Actions tab
2. **Look for error patterns** in the "Check application logs" step
3. **Test locally** with the same environment
4. **Fix the issue** and push again

### Adding new pages:
Update `.github/workflows/pr-build-test.yml` to test your new endpoint:
```bash
# Add to "Test application endpoints" step
curl -f -s http://localhost:8080/your-new-page > /dev/null
```

## 🚨 Error Detection Features

### Enhanced logging in debug mode:
- More verbose error messages
- Service status checks
- Database connectivity validation
- Redis connection testing

### Health check endpoint:
```bash
curl http://localhost:8080/health
```
Returns:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-15 10:30:00"
}
```

## 📊 Understanding CI Results

### ✅ Green (Success):
- All services started correctly
- All endpoints returned HTTP 200
- No critical errors in logs
- Application is ready for review

### ❌ Red (Failure):
- Service startup failed
- Endpoint returned error (4xx/5xx)
- Critical errors found in logs
- Build or dependency issues

### 🟡 Yellow (In Progress):
- Tests are currently running
- Wait for completion before reviewing

## 🔧 Troubleshooting Common Issues

### "Service startup timeout"
- Services took too long to start
- Usually indicates resource constraints or configuration issues
- Check Docker resource limits

### "Database connection failed"
- PostgreSQL service didn't start properly
- Environment variables might be incorrect
- Check database initialization logs

### "Endpoint test failed"
- Application returned error status
- Check application logs for Python exceptions
- Verify all dependencies are properly installed

### "Redis connection failed"
- Redis service startup issue
- Password configuration problem
- Check Redis service logs

### "Nightly dependency test failed"
- **Security vulnerabilities found** - Check the safety report artifact
- **Breaking changes in packages** - Review the workflow logs for specific errors
- **Dependency conflicts** - Check pip compatibility issues in logs
- **New package versions incompatible** - Pin problematic packages in requirements.txt
- **Application errors with latest deps** - Test locally with updated dependencies

## 📈 Best Practices

### Before creating a PR:
1. Test locally with `docker compose up --build` or `podman compose up --build`
2. Check all pages load without errors
3. Review application logs for warnings
4. Ensure new dependencies are in `requirements.txt`

### When CI fails:
1. Don't ignore failures - they catch real issues
2. Check logs thoroughly before asking for help
3. Test the fix locally before pushing again
4. Consider if new tests are needed for your changes

### For dependency changes:
1. Pin specific versions in `requirements.txt`
2. Monitor nightly test results for compatibility issues
3. Update documentation if new env vars are needed
4. Test security implications with `safety check`
5. Use `uv` for faster local dependency testing

## 🎯 Goals of CI Testing

- **Catch build issues early** before they reach production
- **Ensure all pages load** without critical errors
- **Validate dependencies** work together correctly
- **Provide fast feedback** to developers
- **Maintain application stability** across changes

The CI system is designed to give you confidence that your changes work correctly and don't break existing functionality. Use it as a safety net and debugging tool!

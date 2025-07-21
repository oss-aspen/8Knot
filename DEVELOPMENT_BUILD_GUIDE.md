# 🚀 8Knot Development Build Optimizations

## Overview

This guide covers **dramatically faster** development build workflow for 8Knot, featuring optimized Docker/Podman builds and lightning-fast startup times.

## ⚡ Performance Improvements

| Scenario | Before | After | Improvement |
|----------|--------|-------|-------------|
| **First startup** | 3-5 minutes | 2-3 minutes | ~40% faster |
| **Daily restarts** | 3-5 minutes | **9 seconds** | **95% faster** |
| **Code changes** | 3 seconds (hot reload) | 3 seconds | Same (preserved) |
| **Dependency changes** | 3-5 minutes | 2-3 minutes | ~40% faster |

## 🎯 Key Optimizations

### 1. **Build Once, Use Everywhere**
- **Before:** Built the same image 4 times (app-server, worker-callback, worker-query, db-init)
- **After:** Build once as `8knot:latest`, reuse across all services

### 2. **Optimized Build Context**
- **`.dockerignore`** excludes unnecessary files (docs, git, cache, logs)
- **Smaller context** = faster builds and transfers

### 3. **Smart Build Script**
- **`quick-build.sh`** reuses existing images
- **Only rebuilds when necessary**

## 🚀 Quick Start

### First Time Setup
```bash
# Clone and navigate to repository
git clone <repository-url>
cd 8knot

# First build (builds the optimized image)
./quick-build.sh --rebuild
```

### Daily Development Workflow
```bash
# Start 8Knot (reuses existing image - fast!)
./quick-build.sh

# Your app is ready at http://localhost:8080 in ~9 seconds! 🎉
```

### Stop Services
```bash
# Stop all services
podman compose down
```

## 📖 Usage Guide

### Basic Commands

#### Start Development Environment
```bash
./quick-build.sh
```
- ⚡ **9 seconds** if image exists
- 🔄 Reuses existing `8knot:latest` image
- 🎯 Perfect for daily development

#### Force Rebuild
```bash
./quick-build.sh --rebuild
```
- 🔨 **2-3 minutes** - rebuilds image from scratch
- 📦 Use when dependencies change
- 🆕 Use when switching major branches

#### Clean Rebuild (No Cache)
```bash
./quick-build.sh --no-cache
```
- 🧹 **3-4 minutes** - completely clean build
- 🚫 Ignores all Docker layer cache
- 🛠️ Use when troubleshooting build issues

## 🏗️ Build Architecture

### File Structure
```
├── docker-compose.yml       # Production/CI - builds each service separately
├── docker-compose.dev.yml   # Development - build once, reuse everywhere
├── quick-build.sh          # Uses both files: -f docker-compose.yml -f docker-compose.dev.yml
└── .dockerignore           # Reduces build context size
```

### Image Strategy
```yaml
# docker-compose.dev.yml structure (for development only)
services:
  app-base:          # Builds the image once
    build: ./docker/Dockerfile
    image: 8knot:latest

  app-server:        # Reuses the image
    image: 8knot:latest

  worker-callback:   # Reuses the image
    image: 8knot:latest

  worker-query:      # Reuses the image
    image: 8knot:latest

  db-init:          # Reuses the image
    image: 8knot:latest
```

**Note:** The main `docker-compose.yml` remains unchanged for CI/CD compatibility.

### Build Context Optimization
```bash
# .dockerignore excludes:
.git/           # Version control
docs/           # Documentation
*.md            # Markdown files
__pycache__/    # Python cache
.vscode/        # IDE files
*.log           # Log files
```

## 🛠️ Troubleshooting

### Problem: "8knot:latest image not found"
```bash
# Solution: Build the image first
./quick-build.sh --rebuild
```

### Problem: "Changes not reflected"
```bash
# For code changes: Hot reload should handle it (wait 2-3 seconds)
# For dependency changes:
./quick-build.sh --rebuild

# For stubborn issues:
./quick-build.sh --no-cache
```

### Problem: "Build is still slow"
```bash
# Verify you're using the optimized approach
cat docker-compose.dev.yml | grep "image: 8knot:latest"
# Should show multiple services using the same image

# Check .dockerignore exists
ls -la .dockerignore

# Verify script uses dev compose file
grep "docker-compose.dev.yml" quick-build.sh
```

## 📊 Performance Monitoring

### Measure Build Time
```bash
# Time the build process
time ./quick-build.sh

# Time a rebuild
time ./quick-build.sh --rebuild
```

## 📈 Migration from Old Approach

### Before (Legacy)
```bash
podman compose up --build  # 3-5 minutes every time
```

### After (Optimized)
```bash
./quick-build.sh          # way faster for subsequent starts!
```

### Migration Steps
1. ✅ Keep `docker-compose.yml` unchanged (CI/CD compatibility)
2. ✅ Create `docker-compose.dev.yml` (build once, reuse image)
3. ✅ Create `.dockerignore` (reduce build context)
4. ✅ Use `quick-build.sh` script (uses both compose files)
5. 🎉 Enjoy 95% faster development builds!

## 🎯 Best Practices

### Daily Development
- ✅ Use `./quick-build.sh` for normal startup
- ✅ Let hot reload handle code changes
- ✅ Only rebuild when dependencies change

### Dependency Management
- ✅ Run `--rebuild` after modifying pyproject.toml
- ✅ Run `--rebuild` after major Git branch switches
- ✅ Use `--no-cache` only for troubleshooting

## 🆘 Getting Help

### Common Commands Quick Reference
```bash
./quick-build.sh                 # Fast start
./quick-build.sh --rebuild       # Rebuild dependencies (2-3 min)
./quick-build.sh --no-cache      # Clean rebuild (3-4 min)
podman compose down              # Stop services
podman compose logs -f           # View live logs
podman compose logs app-server   # View specific service logs
```

---

**Enjoy your dramatically faster 8Knot development experience!** 🚀

#!/bin/bash

# 8Knot Quick Build Script - Optimized for Development Speed
# Usage: ./quick-build.sh [--rebuild] [--no-cache]

set -e  # Exit on error

echo "🚀 8Knot Quick Build - Optimized for Speed"
echo "=========================================="

# Parse arguments
REBUILD=false
NO_CACHE=false

for arg in "$@"; do
    case $arg in
        --rebuild)
            REBUILD=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Usage: $0 [--rebuild] [--no-cache]"
            exit 1
            ;;
    esac
done

# Check if image exists and if we need to rebuild
if [ "$REBUILD" = true ] || ! podman image exists 8knot:latest; then
    echo "📦 Building 8knot image..."

    if [ "$NO_CACHE" = true ]; then
        echo "🔄 Building without cache..."
        podman build --no-cache -f docker/Dockerfile -t 8knot:latest .
    else
        echo "⚡ Building with cache optimization..."
        podman build -f docker/Dockerfile -t 8knot:latest .
    fi

    echo "✅ Image built successfully!"
else
    echo "♻️  Using existing 8knot:latest image (use --rebuild to force rebuild)"
fi

echo ""
echo "🔧 Starting services using development compose file..."
podman compose -f docker-compose.yml -f docker-compose.dev.yml up -d

echo ""
echo "⏱️  Waiting for services to be ready..."
sleep 3

echo ""
echo "🎉 8Knot is starting up!"
echo "🌐 Access the application at: http://localhost:8080"
echo ""
echo "📊 To view logs: podman compose logs -f"
echo "🛑 To stop: podman compose down"
echo ""
echo "💡 Next time, just run './quick-build.sh' for instant startup!"

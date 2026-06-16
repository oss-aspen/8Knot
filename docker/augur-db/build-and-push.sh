#!/usr/bin/env bash
# Build the pre-populated min_db image and push it to GHCR.
# Run this from a machine that has the data dump locally (it is never committed).
#
# One-time setup:
#   echo "$GHCR_PAT" | docker login ghcr.io -u <your-github-username> --password-stdin
#   (PAT needs write:packages scope)
#
# Usage:
#   docker/augur-db/build-and-push.sh
#
# After the first push, make the package public once in GitHub:
#   github.com/orgs/oss-aspen/packages -> 8knot-min-db -> Package settings -> Change visibility

set -euo pipefail

IMAGE="${IMAGE:-ghcr.io/oss-aspen/8knot-min-db:latest}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$SCRIPT_DIR/init/03_data.sql" ]; then
    echo "ERROR: $SCRIPT_DIR/init/03_data.sql not found." >&2
    echo "Copy the Augur data dump there before building (it is gitignored)." >&2
    exit 1
fi

echo "Building $IMAGE ..."
docker build -t "$IMAGE" "$SCRIPT_DIR"

echo "Pushing $IMAGE ..."
docker push "$IMAGE"

echo "Done. Users can now: docker compose up"

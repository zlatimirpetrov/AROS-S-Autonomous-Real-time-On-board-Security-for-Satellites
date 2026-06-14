#!/usr/bin/env bash
# Run AROS-S in a hardened container.
# Usage: ./run.sh [--mitigation on|off] [any other src.main args]
set -euo pipefail

podman run --rm \
  --read-only \
  --tmpfs /tmp \
  --tmpfs /app/logs \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --memory=256m \
  --cpus=0.5 \
  --pids-limit=64 \
  -p 5005:5005/udp \
  --add-host=host.containers.internal:host-gateway \
  -e AROS_CMD_HOST=host.containers.internal \
  --env-file .env \
  aros-s "$@"
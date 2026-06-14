# Run AROS-S in a hardened container (Windows / PowerShell).
# Usage: .\run.ps1 --mitigation off
podman run --rm `
  --read-only `
  --tmpfs /tmp --tmpfs /app/logs `
  --cap-drop=ALL --security-opt=no-new-privileges `
  --memory=256m --cpus=0.5 --pids-limit=64 `
  -p 5005:5005/udp `
  --add-host=host.containers.internal:host-gateway `
  -e AROS_CMD_HOST=host.containers.internal `
  --env-file .env `
  aros-s $args
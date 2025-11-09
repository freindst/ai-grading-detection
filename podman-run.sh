#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

IMAGE_NAME=${IMAGE_NAME:-grading-assistant}
CONTAINER_NAME=${CONTAINER_NAME:-grading-assistant}
DATA_DIR=${DATA_DIR:-${PROJECT_ROOT}/data}
ENV_FILE=${ENV_FILE:-${PROJECT_ROOT}/.env}

if [ ! -d "${DATA_DIR}" ]; then
  mkdir -p "${DATA_DIR}"
fi

# Determine default Ollama host for the container.
# - Native Podman on Windows/macOS: host.containers.internal resolves to the host OS
# - WSL workflow (legacy): fall back to detected Windows host IP
DEFAULT_OLLAMA_HOST="http://host.containers.internal:11434"

if [ -z "${OLLAMA_HOST:-}" ]; then
  if [ -f /proc/version ] && grep -qi "microsoft" /proc/version; then
    WINDOWS_IP=$(ip route | awk '/default/ {print $3; exit}')
    if [ -n "${WINDOWS_IP}" ]; then
      DEFAULT_OLLAMA_HOST="http://${WINDOWS_IP}:11434"
    fi
  fi
  OLLAMA_HOST="${DEFAULT_OLLAMA_HOST}"
fi

podman build \
  --pull=missing \
  -t "${IMAGE_NAME}" \
  -f "${PROJECT_ROOT}/Containerfile" \
  "${PROJECT_ROOT}"

RUN_ARGS=(
  --rm
  --name "${CONTAINER_NAME}"
  -p 7860:7860
  -v "${DATA_DIR}:/app/data:Z"
)

if [ -f "${ENV_FILE}" ]; then
  RUN_ARGS+=(--env-file "${ENV_FILE}")
fi

RUN_ARGS+=(
  -e "OLLAMA_HOST=${OLLAMA_HOST}"
)

podman run "${RUN_ARGS[@]}" "${IMAGE_NAME}"


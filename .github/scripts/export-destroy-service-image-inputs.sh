#!/usr/bin/env bash
set -euo pipefail

target="${1:?Terraform target is required}"
placeholder_digest="sha256:0000000000000000000000000000000000000000000000000000000000000000"

case "$target" in
  backend-service)
    echo "TF_VAR_backend_image_digest=$placeholder_digest"
    ;;
  frontend-service)
    echo "TF_VAR_frontend_image_digest=$placeholder_digest"
    ;;
esac

#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
helper="$script_dir/export-destroy-service-image-inputs.sh"
placeholder_digest="sha256:0000000000000000000000000000000000000000000000000000000000000000"

test_backend_service_exports_backend_digest() {
  actual="$(bash "$helper" backend-service)"
  expected="TF_VAR_backend_image_digest=$placeholder_digest"
  test "$actual" = "$expected"
}

test_frontend_service_exports_frontend_digest() {
  actual="$(bash "$helper" frontend-service)"
  expected="TF_VAR_frontend_image_digest=$placeholder_digest"
  test "$actual" = "$expected"
}

test_non_service_target_exports_nothing() {
  actual="$(bash "$helper" network)"
  test -z "$actual"
}

test_backend_service_exports_backend_digest
test_frontend_service_exports_frontend_digest
test_non_service_target_exports_nothing

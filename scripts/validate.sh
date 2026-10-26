#!/usr/bin/env bash
set -euo pipefail
: "${APP_URL:?Set APP_URL to the HTTPS application origin}"
kubectl rollout status deployment/backend -n blogapp --timeout=300s
kubectl rollout status deployment/frontend -n blogapp --timeout=300s
curl --fail --silent --show-error --retry 5 --retry-delay 5 "$APP_URL/healthz"
curl --fail --silent --show-error --retry 5 --retry-delay 5 "$APP_URL/api/posts" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert isinstance(d["data"],list)'

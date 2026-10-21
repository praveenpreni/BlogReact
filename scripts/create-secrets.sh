#!/usr/bin/env bash
set -euo pipefail
# Supply values through a protected CI secret store or secret manager, never literal shell history.
: "${DB_PASSWORD:?required}" "${MYSQL_ROOT_PASSWORD:?required}" "${JWT_SECRET:?required}"
umask 077
temp_file=$(mktemp)
trap 'rm -f "$temp_file"' EXIT
printf 'DB_PASSWORD=%s\nMYSQL_ROOT_PASSWORD=%s\nJWT_SECRET=%s\n' "$DB_PASSWORD" "$MYSQL_ROOT_PASSWORD" "$JWT_SECRET" > "$temp_file"
kubectl create secret generic blog-secrets -n blogapp --from-env-file="$temp_file" --dry-run=client -o yaml | kubectl apply -f -

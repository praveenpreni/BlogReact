#!/usr/bin/env bash
set -euo pipefail
: "${ECR_REGISTRY:?required}" "${NEXUS_DOCKER_REGISTRY:?required}" "${IMAGE_TAG:?required}" "${AWS_REGION:?required}"
: "${NEXUS_USER:?required}" "${NEXUS_PASSWORD:?required}"
mkdir -p reports
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"
printf '%s' "$NEXUS_PASSWORD" | docker login "$NEXUS_DOCKER_REGISTRY" --username "$NEXUS_USER" --password-stdin
trap 'docker logout "$NEXUS_DOCKER_REGISTRY" >/dev/null 2>&1 || true; docker logout "$ECR_REGISTRY" >/dev/null 2>&1 || true' EXIT
for component in frontend backend; do
 source_image="$ECR_REGISTRY/blogapp-$component:$IMAGE_TAG"
 nexus_image="$NEXUS_DOCKER_REGISTRY/blogapp-$component:$IMAGE_TAG"
 # Both names reference the same locally built image that passed Trivy.
 docker tag "$source_image" "$nexus_image"
 docker push "$source_image"
 docker push "$nexus_image"
 docker image inspect "$source_image" --format '{{json .RepoDigests}}' > "reports/$component-registry-digests.json"
done
python3 scripts/release-record.py

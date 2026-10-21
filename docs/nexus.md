# Nexus and ECR image publishing

The pipeline publishes the same scanned frontend and backend images to both private ECR and a Nexus Docker hosted repository. EKS pulls from ECR. Nexus additionally retains the release archive. Use the same commit and build tag in all three locations.

Create a Docker hosted repository in Nexus, select a writable blob store, disable redeploy for release tags, and expose its Docker connector behind TLS with a trusted certificate. Enable the Docker Bearer Token Realm. The registry address supplied to Docker must be a hostname and optional port, without https:// or a /repository path. The Nexus raw archive URL is a separate HTTPS /repository/blog-releases URL.

Create a dedicated deployment user with only the browse, read, add and edit permissions needed by these hosted repositories. Store that account in Jenkins as nexus-creds. Put the Docker TLS endpoint into NEXUS_DOCKER_REGISTRY. Do not enable anonymous writes or configure an insecure Docker registry to bypass TLS failures.

After the scan gate passes, scripts/publish-images.sh tags each local image for Nexus and pushes it to both registries. It writes image references and available repository digests to reports/release.json. Capture both registry views and the actual running Deployment image references for E06. A source archive alone is no longer used to satisfy the image requirement.

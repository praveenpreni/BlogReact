# Three-tier Blog Application on Amazon EKS

## Cloud execution — 27 October 2026

- [Live HTTPS application](https://1c3j649rgg.execute-api.ap-south-1.amazonaws.com)
- [Execution report with screenshots](docs/Cloud_Execution_Report.pdf)
- [Cloud screenshots and original result files](docs/cloud-execution-evidence/)
- [Executed architecture and configuration](docs/Cloud_Deployment.md)

React → Express API → MySQL is running on EKS in Mumbai. Jenkins tests the code, enforces an analysis-specific SonarQube gate, builds the two Docker images, blocks HIGH/CRITICAL Trivy findings, publishes both versioned images to Nexus and ECR, updates EKS, and verifies public application operations. EKS pulls immutable image tags from ECR. Nexus also stores the committed source archive.

The complete pipeline has succeeded. The controlled quality and image rejection jobs stopped before deployment. A commit-triggered rolling release served 196 sampled public requests with zero failures. MySQL pod recreation retained the same post, comment and EBS volume; a backup restored successfully to an isolated database with matching table counts. See the report for exact build numbers, source commit, image digests, screenshots and limitations.

## Architecture

Public HTTPS uses API Gateway HTTP API → VPC Link → private ALB Ingress → two frontend pods → two backend pods → MySQL StatefulSet with encrypted EBS storage. Jenkins, SonarQube, Nexus, Prometheus and Grafana are private. Administrative localhost addresses in screenshots require authenticated AWS SSM or Kubernetes forwarding; they are not public review links.

Prometheus/Grafana monitor CPU, memory, readiness, restarts, node health and API latency. Network policies restrict database ingress to backend pods. The release IAM role can publish only to the two ECR repositories and patch application Deployments; it cannot read Kubernetes Secrets, execute in pods or change another namespace.

## Source and deployment

The application is derived from [Vennilavanguvi/BlogReact](https://github.com/Vennilavanguvi/BlogReact), baseline commit recorded in SOURCE.md. Dockerfiles, Jenkinsfile, k8s/, infra/, monitoring/, scripts/ and ops/ are included here. [Executed infrastructure configuration](infra/executed/) records this deployment; replace environment-specific IDs when recreating it.

[Cloud deployment notes](docs/Cloud_Deployment.md) describe the executed HTTPS option. [Domain/ACM deployment recipe](docs/deployment.md), [environment mapping](docs/configuration.md) and [Nexus setup](docs/nexus.md) describe the reusable configuration. Platform bootstrap, repository credentials and Nexus licence acceptance are one-time setup; ordinary releases run through Jenkins.

## Run locally

1. Start a Linux Docker engine or Docker Desktop.
2. Run `python scripts/create-local-env.py` to generate ignored credentials.
3. Run `docker compose --env-file ops/local.env up --build -d`.
4. Open http://localhost:3000 and register an account.
5. Run `APP_URL=http://localhost:3000 python3 scripts/smoke.py` in a Linux shell.

The two .env.example files document the settings. Production configuration comes from backend-config and blog-secrets; real environment and backup files must remain private. The schema initializes tables without hardcoded demo accounts or passwords.

## Scope and limitations

This educational deployment demonstrates production-oriented controls. MySQL and the CI host are single instances; persistence and a tested restore do not provide database high availability. SonarQube enforces its configured new-code gate; overall coverage is 40.6%, with existing reliability findings recorded in the report. Community Build does not provide paid-edition injection analysis. No claim of a fully hardened, highly available production platform is made.

The earlier [22 October native local demonstration](docs/Local_Execution_Report.pdf) is historical. The cloud report supersedes its then-pending cloud status. Resources remain running for tutor review and incur AWS charges until the user requests cleanup.

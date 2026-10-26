# Blog application on Amazon EKS

## Execution evidence - local demonstration

**22 October 2026:** [Open the screenshot report](docs/Local_Execution_Report.pdf), [browse execution screenshots](docs/execution-evidence/), or inspect [raw Jenkins, scan and database results](verification/local-execution/).

The native local run demonstrated a successful Jenkins build, 10 passing tests, a production frontend build, a blocking Trivy dependency gate, real React/Express/MySQL operations, database restart persistence, and backup restoration. A separate vulnerable lockfile fixture was rejected by the gate. [Scope and reproduction details](docs/local-demo.md). Docker images, SonarQube, Nexus/ECR and EKS deployment remain unexecuted; this is not a complete cloud deployment.


Repository: https://github.com/praveenpreni/BlogReact

React frontend, Express API and persistent MySQL, with Docker builds, Jenkins delivery, SonarQube, Trivy, images in both Nexus and ECR, and Prometheus/Grafana resources.

## Run locally

1. Start Docker Desktop or a Linux Docker engine.
2. Run `python scripts/create-local-env.py` once to create ignored strong local credentials.
3. Run `docker compose --env-file ops/local.env up --build -d`.
4. Open http://localhost:3000 and register an account.
5. Run `APP_URL=http://localhost:3000 python3 scripts/smoke.py` in a Linux shell for write/read/comment verification.

Do not remove the mysql-data volume to restart the database. Never share ops/local.env. The production schema creates tables without demo accounts or passwords.

## Deploy to AWS

Read [deployment order](docs/deployment.md), [environment mapping](docs/configuration.md) and [Nexus setup](docs/nexus.md).

Copy infra/deployment.example.json to ignored deployment.json. Review the bootstrap plan before using --apply. The private EKS API requires a host with VPC connectivity. The cluster template configures the managed EBS CSI driver with dedicated IAM, metrics-server and VPC CNI policy enforcement. The bootstrap installs the ALB controller, monitoring, certificate validation, DNS, registries and application resources.

The Jenkinsfile tests, enforces SonarQube quality, builds and scans images, archives the committed source to Nexus, and publishes the same scanned frontend and backend images to both Nexus and ECR. Main releases update EKS workloads and run application validation. Configure the real endpoints and protected credentials in Jenkins. EKS pulls from ECR.

## Verification

See verification/STATUS.md and the saved test and dependency reports. Backend tests use Node native coverage and emit LCOV for SonarQube. Both full dependency audits are clean as of the recorded run; Trivy must still evaluate the built images.

The database is single replica. Persistence is not high availability or an independent backup. Complete database restart, restore, network rejection, rolling traffic, failed gate and real monitoring demonstrations before claiming project acceptance.

Deployment results and screenshots must come from actual execution. No live application URL or successful cloud deployment is claimed by these source files.

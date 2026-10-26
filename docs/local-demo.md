# Local execution demonstration - 22 October 2026

This run uses native Windows processes. It does not establish Docker or EKS execution.

- React/Vite application: http://localhost:3000
- Express API: http://localhost:5000, database readiness `/readyz`, metrics `/metrics`
- Isolated MySQL 8.0.42: 127.0.0.1:13306, dedicated local data directory
- Jenkins 2.580.1: http://localhost:18080
- Successful Jenkins Freestyle job: BlogApp-Local-Demonstration, build 2
- Expected failed fixture job: BlogApp-Local-Gate-Rejection, build 1

The successful job ran 7 backend tests, 3 frontend tests, a Vite production build, a Trivy 0.76.1 dependency gate including development dependencies, and registration/post/read/comment smoke operations against real MySQL. Both package-lock files had zero HIGH or CRITICAL findings. This was a filesystem dependency scan, not an image scan. Backend unit tests mock the database; the smoke test provides the separate real database check.

The browser-created proof post (ID 1) and its comment survived a MySQL restart using the same data directory. Readiness returned 503 while MySQL was stopped, liveness remained 200, and recovery after starting the database took 2.09 seconds in this observation. Database requests failed during the controlled outage; zero-downtime deployment is not claimed. A consistent mysqldump was restored into a separate blogdb_restore database with matching user/post/comment counts (2/2/2 at capture) and matching proof-post title/body.

The negative gate scans an isolated lockfile referencing lodash 4.17.20. It finds two HIGH/CRITICAL advisories and Jenkins marks the job FAILURE. No vulnerable dependency was installed or executed. This proves local scan rejection, not a deployed-image failure or a SonarQube quality gate.

## Reproduction

Use Node 22.12+ (the captured run used Node 24.19), Python 3, MySQL, Trivy and Jenkins with a supported Java runtime. Install locked frontend/backend dependencies. Initialize a separate MySQL data directory and import database/init.sql, create a scoped application user and generate strong database/JWT secrets outside Git. Set backend configuration according to .env.example and start src/server.js on port 5000. Start Vite on loopback port 3000; its existing proxy forwards /api to the backend.

Set DEMO_NODE_PATH, DEMO_TRIVY_PATH, TRIVY_CACHE_DIR and APP_URL=http://localhost:3000 for a Jenkins Windows batch build that runs `python ops/local-ci.py`. The native helper requires installed dependencies and a running application. Configure a dedicated Jenkins local account and loopback-only access. Archive backend/coverage/lcov.info and reports/trivy-local.json. Do not use the EKS Jenkinsfile as the local job: it requires AWS, containers, SonarQube and Nexus.

## Evidence and scope

See [the screenshot report](Local_Execution_Report.pdf), [screenshots](execution-evidence/) and [raw execution records](../verification/local-execution/). Localhost URLs work only while services are running on the demonstration computer. The PDF and screenshots remain reviewable without access to that computer.

Docker Desktop failed to open and its Linux engine was unavailable. SonarQube, Nexus publishing, ECR publishing, Kubernetes/EKS, Grafana dashboards, controller installation, NetworkPolicy enforcement and rolling deployment were not executed in this local run. The prior incomplete AWS cluster was removed at the owner's request. This report is a local execution supplement, not full acceptance of the original cloud brief.

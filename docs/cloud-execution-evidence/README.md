# Cloud Deployment Evidence

Source commit: `00bfc302acd73933912fd12579b72885081d22cb`.
Jenkins release build: **14 SUCCESS**. Immutable image tag: `00bfc302acd7-14`.

[CI/CD Deployment Report](../Cloud_Execution_Report.pdf) contains the architecture, implementation details, validation results, execution screenshots and operational scope.

| Evidence | Coverage |
|---|---|
| E01 | Source repository and release traceability |
| E02 | Container builds and runtime hardening |
| E03 | CI/CD pipeline, storage and database initialization |
| E04 | SonarQube analysis and positive/negative gate tests |
| E05 | Versioned images and digests in ECR and Nexus |
| E06 | Application image Trivy scans and vulnerable-image rejection |
| E07 | EKS resources, replicas, probes, image tags and routing |
| E08 | Public application and three-tier integration |
| E09 | Database pod recreation and persistent data |
| E10 | Rolling deployment and request sampling |
| E11 | IAM, RBAC, configuration and Secret metadata |
| E12 | NetworkPolicy inventory and connection tests |
| E13 | Prometheus, Grafana and alert evaluation |
| E14 | Timestamped application logs |
| E15 | Database backup and isolated restore |

PNG files capture the deployed application, AWS console, Jenkins and live command execution. S-prefixed files contain command and infrastructure views associated with the same release. Raw files preserve timestamps, commands, exit codes and results. The live command console executes kubectl subprocesses and streams output. Enlarged NetworkPolicy details in the PDF are cropped from the included full-resolution screenshot.

Build #12 served 196/196 HTTP 200 requests during its automated rollout. A separate redeployment of the build #14 images served 96/96 HTTP 200 requests. Database validation records each recreation run separately, including unchanged storage and retained application content.

The SonarQube new-code gate passed; overall coverage is 40.6% with existing findings documented in the report. MySQL uses a single StatefulSet instance with encrypted persistent storage. Database high availability is outside this implementation.

Documentation commits are separate from the tested release source. The manifest records SHA-256 hashes for the evidence files. Credentials, kubeconfig and private SQL backups are excluded.

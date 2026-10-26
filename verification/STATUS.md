# Cloud verification status — 27 October 2026

- Complete Jenkins GitHub-to-EKS pipeline: SUCCESS.
- Backend 7 tests and frontend 3 tests: PASS.
- Current SonarQube analysis-specific new-code Quality Gate: PASS. Overall coverage 40.6%; existing reliability findings are disclosed, not marked fixed.
- Separate deliberately untested Sonar fixture: gate ERROR; deployment skipped.
- Frontend and backend Docker image scans: zero HIGH/CRITICAL vulnerabilities at the recorded run; both image builds and non-root runtime configurations verified.
- Deliberately vulnerable image fixture: rejected; deployment skipped.
- Versioned source archive and frontend/backend images: published to Nexus; same image tags/digests published to ECR and used by EKS.
- Public HTTPS registration, login, post creation/read and comments: PASS.
- Rolling release traffic: 196 HTTP 200 responses, zero failures.
- MySQL pod recreation: new pod UID, unchanged persistent volume, same stored post/comment retained; recovery 28.98 seconds.
- Backup restored to a separate database: users/posts/comments matched 3/5/5 at the snapshot.
- NetworkPolicy: unrelated client denied to MySQL/backend; intended frontend/backend traffic allowed.
- Release RBAC: Secrets read, pod execution and changes in another namespace denied.
- Prometheus/Grafana: all six dashboard queries returned data; controlled synthetic alert fired and was removed.
- Frontend, backend, MySQL and Kubernetes resource/log records captured.

See docs/Cloud_Execution_Report.pdf and docs/cloud-execution-evidence/ for timestamps, source commit, final build/image records and genuine screenshots. Earlier local-only evidence remains historical and is not represented as cloud execution.

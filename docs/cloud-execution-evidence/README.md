# Executed cloud evidence

Acceptance source: `00bfc302acd73933912fd12579b72885081d22cb`.
Jenkins acceptance build: **14 SUCCESS**, image tag `00bfc302acd7-14`.

Read [the 28-page execution report](../Cloud_Execution_Report.pdf) for the requirement map, actual screenshots, results and limitations. PNGs are genuine captures of the deployed application and tools. Raw JSON, logs and console records accompany the screenshots; E14 is explicitly a screenshot of a recorded real logging execution file.

E01 source; E02 container hardening; E03 pipeline and database storage; E04 Sonar positive/negative gates; E05 both registries; E06 Trivy positive/negative gates; E07 EKS workloads; E08 application integration; E09 persistence; E10 rolling traffic; E11 IAM/RBAC/configuration; E12 NetworkPolicy; E13 monitoring/alert; E14 logging; E15 backup restore.

The 196-request rolling test records build 12. Final acceptance build 14 uses the same readiness and draining controls. Historical failed scans demonstrate blocked deployment. Overall Sonar coverage is 40.6% with existing issues; the passed new-code gate does not imply a clean overall codebase. MySQL is a single-instance demonstration with persistent storage, not a highly available database.

Documentation publication may advance the repository main branch beyond the pinned acceptance source. No credentials, private backup SQL or kubeconfig are included.

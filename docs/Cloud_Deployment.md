# Executed cloud deployment

Execution date: 26–27 October 2026 (Asia/Kolkata). Personal AWS account 782610231927; region ap-south-1. The institute account was not used for this deployment.

## Application entry point

https://1c3j649rgg.execute-api.ap-south-1.amazonaws.com

API Gateway provides the AWS-managed public HTTPS certificate. A VPC Link reaches the port-80 listener of the internal ALB created by EKS Ingress blogapp. The integration forwards all methods and rewrites the origin path to $request.path. There is no public ALB listener, database or administrative endpoint. The private hop from API Gateway to ALB is HTTP; this is not an end-to-end TLS claim.

CloudFront distribution creation was unavailable until AWS account verification, so the executed architecture uses API Gateway. The unused CloudFront VPC origin was removed. No custom domain or ACM certificate was required. The domain/ACM recipe in deployment.md is an alternative, not the deployed entry point.

## Infrastructure actually configured

- EKS blogapp-eks, Kubernetes 1.35 (standard support), two private t3.large workers across two Availability Zones; encrypted gp3 node disks and IMDSv2.
- Managed VPC CNI with NetworkPolicy enforcement, CoreDNS, kube-proxy, metrics-server and EBS CSI. Dedicated service-account IAM roles are used by CNI, EBS CSI and the load balancer controller.
- AWS Load Balancer Controller chart 3.6.2, app v3.6.2; kube-prometheus-stack chart 92.14.0.
- Single NAT gateway for worker and private CI egress. Cluster API is private plus a public endpoint restricted to the operator's single IP CIDR.
- Private t3.xlarge CI host, encrypted 100 GiB root disk, no inbound security-group rules. Administrative access uses authenticated SSM forwarding.
- Jenkins, SonarQube Community Build 26.10.0.133078 with PostgreSQL 17, and Nexus Community Edition 3.97.2. Their volumes persist on the encrypted CI disk. Nexus uses a protected project-specific encryption key and its Docker endpoint uses a private CA trusted by the build tools.
- MySQL 8.4 StatefulSet, 20 GiB encrypted gp3 PVC. Prometheus 15 GiB, Grafana 5 GiB, Alertmanager 2 GiB persistent volumes. The StorageClass uses Retain; retained volumes need explicit cleanup.
- EKS API, audit and authenticator logs in CloudWatch; application logs are available through kubectl. The application logs do not record Authorization headers or password values.

The exact non-secret executed resource settings are in infra/executed/. The cluster example deliberately replaces the operator's personal IP with REPLACE_OPERATOR_IPV4/32. Resource IDs in the execution records identify this environment and must be replaced when recreating it.

## Environment-file mapping

frontend/.env.example sets VITE_API_URL=/api. The production bundle uses this relative URL; Nginx forwards /api to backend-service:5000 through Kubernetes DNS. No browser-visible API credential is embedded.

backend/.env.example documents PORT, DB_HOST, DB_PORT, DB_USER, DB_NAME and CORS_ORIGIN; backend-config supplies those non-secret values. Production DB_PASSWORD and JWT_SECRET come from blog-secrets. MYSQL_ROOT_PASSWORD is supplied to the database from that Secret. Strong values were generated once, stored in AWS Secrets Manager and injected without publishing their values. No actual .env or secret backup is included in the repository.

## Release flow and acceptance

GitHub main is indexed automatically by Jenkins. A release tag combines its 12-character source commit and Jenkins build number. SonarQube analysis is followed by polling that specific analysis's Quality Gate; a non-OK result blocks the pipeline. Polling avoids exposing private Jenkins to incoming webhooks. Both images then pass the HIGH/CRITICAL Trivy gate before the source archive and images can be published to Nexus/ECR.

Kubernetes application resources are bootstrapped once by the platform operator. The restricted CI identity updates their image versions and performs rollout and public smoke validation. It cannot create arbitrary workloads, retrieve Secrets or execute inside pods. The configured negative-test jobs are preserved in verification/cloud/.

The initial rollout validation saw a transient 502. Frontend ALB pod readiness gates, 20-second target draining, 25-second frontend preStop, 10-second backend preStop and 60-second pod termination grace were then configured. The next commit-triggered rollout passed all 196 sampled HTTP requests with zero failures. The report preserves the actual result, rather than claiming a theoretical downtime guarantee.

A controlled synthetic Prometheus alert was observed firing and then removed. This demonstrated rule evaluation and cleanup, without claiming a production incident or external email notification. Grafana queries for all six application panels returned data.

## Review and cleanup

The application URL is public. CI, quality, repository and monitoring UIs stay private; screenshots and original execution records provide review evidence without exposing credentials.

After tutor approval, remove the API Gateway API and VPC Link, application Ingress/ALB, monitoring resources, CI instance and its volumes, EKS node group/cluster and dedicated networking/NAT. Check retained MySQL/monitoring EBS volumes, ECR images, project IAM roles/policies/access entries, the project Secrets Manager secret and CloudWatch log group. Verify the resource inventory before removing project-specific security groups. No unrelated AWS resources or institute resources should be deleted.

No automatic cleanup is scheduled: the user asked to keep the deployment for tutor approval. The earlier daily estimate was about US$15–20 while this environment runs; actual AWS usage is authoritative.

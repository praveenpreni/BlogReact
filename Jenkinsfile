pipeline {
 agent { label 'blog-ci' }
 options { disableConcurrentBuilds(); timeout(time: 45, unit: 'MINUTES') }
 parameters {
  string(name: 'AWS_REGION', defaultValue: 'ap-south-1')
  string(name: 'EKS_CLUSTER', defaultValue: 'blogapp-eks')
  string(name: 'ECR_REGISTRY', defaultValue: env.BLOG_ECR_REGISTRY ?: 'REPLACE_ACCOUNT.dkr.ecr.ap-south-1.amazonaws.com')
  string(name: 'APP_URL', defaultValue: env.BLOG_APP_URL ?: 'https://REPLACE_DOMAIN')
  string(name: 'NEXUS_URL', defaultValue: env.BLOG_NEXUS_URL ?: 'https://REPLACE_NEXUS/repository/blog-releases')
  string(name: 'NEXUS_DOCKER_REGISTRY', defaultValue: env.BLOG_NEXUS_DOCKER_REGISTRY ?: 'REPLACE_NEXUS_DOCKER_HOST:PORT')
 }
 environment {
  AWS_REGION = "${params.AWS_REGION ?: 'ap-south-1'}"
  EKS_CLUSTER = "${params.EKS_CLUSTER ?: 'blogapp-eks'}"
  ECR_REGISTRY = "${params.ECR_REGISTRY ?: env.BLOG_ECR_REGISTRY}"
  APP_URL = "${params.APP_URL ?: env.BLOG_APP_URL}"
  NEXUS_URL = "${params.NEXUS_URL ?: env.BLOG_NEXUS_URL}"
  NEXUS_DOCKER_REGISTRY = "${params.NEXUS_DOCKER_REGISTRY ?: env.BLOG_NEXUS_DOCKER_REGISTRY}"
 }
 stages {
  stage('Checkout') { steps { checkout scm; script { env.IMAGE_TAG = sh(script: 'git rev-parse --short=12 HEAD', returnStdout:true).trim() + '-' + env.BUILD_NUMBER } } }
  stage('Build and test') { steps { sh 'mkdir -p reports; cd backend && npm ci && npm test'; sh 'cd frontend && npm ci && npm test && npm run build' } }
  stage('SonarQube') { steps { script { def scanner = tool 'SonarScanner'; withSonarQubeEnv('sonarqube-server') { sh "${scanner}/bin/sonar-scanner" } } } }
  stage('Quality gate') { steps { timeout(time:10,unit:'MINUTES') { withSonarQubeEnv('sonarqube-server') { sh 'python3 scripts/quality-gate.py' } } } }
  stage('Build images') { steps { sh '''
   docker build -t "$ECR_REGISTRY/blogapp-backend:$IMAGE_TAG" backend
   docker build -t "$ECR_REGISTRY/blogapp-frontend:$IMAGE_TAG" frontend
  ''' } }
  stage('Trivy gate') { steps { sh '''
   set -eu
   scan_status=0
   for component in frontend backend; do
     trivy image --exit-code 1 --severity HIGH,CRITICAL --format json --output "reports/trivy-$component.json" "$ECR_REGISTRY/blogapp-$component:$IMAGE_TAG" || scan_status=1
   done
   exit "$scan_status"
  ''' } }
  stage('Nexus release archive') { when { branch 'main' }
   steps { withCredentials([usernamePassword(credentialsId:'nexus-creds',usernameVariable:'NEXUS_USER',passwordVariable:'NEXUS_PASSWORD')]) { sh '''
   set -eu
   git archive --format=tar.gz --output="reports/blog-$IMAGE_TAG.tgz" HEAD
   curl --fail --silent --show-error --user "$NEXUS_USER:$NEXUS_PASSWORD" --upload-file "reports/blog-$IMAGE_TAG.tgz" "$NEXUS_URL/blog-$IMAGE_TAG.tgz"
  ''' } } }
  stage('Publish to ECR and Nexus') { when { branch 'main' }
   steps { withCredentials([usernamePassword(credentialsId:'nexus-creds',usernameVariable:'NEXUS_USER',passwordVariable:'NEXUS_PASSWORD')]) { sh 'bash scripts/publish-images.sh' } } }
  stage('Deploy main') { when { branch 'main' }
   steps { sh '''
   set -eu
   aws eks update-kubeconfig --name "$EKS_CLUSTER" --region "$AWS_REGION"
   kubectl set image deployment/backend backend="$ECR_REGISTRY/blogapp-backend:$IMAGE_TAG" -n blogapp
   kubectl set image deployment/frontend frontend="$ECR_REGISTRY/blogapp-frontend:$IMAGE_TAG" -n blogapp
   bash scripts/validate.sh
   python3 scripts/smoke.py
   python3 scripts/collect-evidence.py --routine --out reports/evidence
  ''' } }
 }
 post { always { archiveArtifacts artifacts:'reports/**,backend/coverage/**',allowEmptyArchive:true; sh 'docker logout "$ECR_REGISTRY" || true' } }
}

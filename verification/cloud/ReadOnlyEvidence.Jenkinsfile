pipeline {
 agent { label 'blog-ci' }
 stages {
  stage('Read EKS workloads') { steps { sh '''
   set -eu
   mkdir -p reports
   aws eks update-kubeconfig --name blogapp-eks --region ap-south-1
   kubectl get deploy,pod,svc,ingress -n blogapp -o wide | tee reports/workloads.txt
   kubectl get deployment backend frontend -n blogapp -o json > reports/deployment-runtime.json
   kubectl rollout status deployment/backend -n blogapp --timeout=120s
   kubectl rollout status deployment/frontend -n blogapp --timeout=120s
  ''' } }
  stage('Inspect deployed container hardening') { steps { sh '''
   set -eu
   for component in frontend backend; do
     image=$(kubectl get deployment "$component" -n blogapp -o jsonpath='{.spec.template.spec.containers[0].image}')
     echo "Deployed $component image: $image"
     docker image inspect "$image" --format 'Runtime user={{.Config.User}}; image bytes={{.Size}}; healthcheck={{json .Config.Healthcheck}}'
   done
  ''' } }
  stage('Verify least privilege') { steps { sh '''
   set -eu
   echo 'The release identity must NOT read application Secrets:'
   if kubectl get secrets -n blogapp > reports/secrets-denied.txt 2>&1; then exit 1; fi
   cat reports/secrets-denied.txt
   echo 'The release identity must NOT execute commands inside application pods:'
   if kubectl auth can-i create pods/exec -n blogapp; then exit 1; fi
   echo 'The release identity may patch only application deployments:'
   kubectl auth can-i patch deployments -n blogapp
   echo 'The release identity must NOT patch another namespace:'
   if kubectl auth can-i patch deployments -n default; then exit 1; fi
  ''' } }
 }
 post { always { archiveArtifacts artifacts:'reports/**',allowEmptyArchive:true } }
}
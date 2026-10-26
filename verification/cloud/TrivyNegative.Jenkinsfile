pipeline {
 agent { label 'blog-ci' }
 options { timeout(time:15, unit:'MINUTES') }
 stages {
  stage('Build isolated vulnerable fixture') { steps { sh '''
   set -eu
   mkdir -p reports fixture
   printf 'FROM node:22-alpine\nWORKDIR /fixture\nRUN npm init -y && npm install --omit=dev lodash@4.17.20\nUSER node\n' > fixture/Dockerfile
   docker build -t blogapp-trivy-negative:fixture fixture
  ''' } }
  stage('Reject HIGH and CRITICAL vulnerabilities') { steps { sh 'trivy image --severity HIGH,CRITICAL --exit-code 1 --format json --output reports/trivy-rejected-image.json blogapp-trivy-negative:fixture' } }
  stage('Deployment must never run') { steps { error 'Negative vulnerability gate did not reject the fixture' } }
 }
 post { always { archiveArtifacts artifacts:'reports/**',allowEmptyArchive:true } }
}
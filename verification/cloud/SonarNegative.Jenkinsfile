pipeline {
 agent { label 'blog-ci' }
 options { timeout(time:15,unit:'MINUTES') }
 stages {
  stage('Prepare isolated untested source') { steps {
   sh 'mkdir -p fixture'
   writeFile file:'fixture/classify.js', text:'''export function classify(value) {
  if (value === 0) return 0;
  if (value === 1) return 1;
  if (value === 2) return 2;
  if (value === 3) return 3;
  if (value === 4) return 4;
  if (value === 5) return 5;
  if (value === 6) return 6;
  if (value === 7) return 7;
  if (value === 8) return 8;
  if (value === 9) return 9;
  if (value === 10) return 10;
  if (value === 11) return 11;
  if (value === 12) return 12;
  if (value === 13) return 13;
  if (value === 14) return 14;
  if (value === 15) return 15;
  if (value === 16) return 16;
  if (value === 17) return 17;
  if (value === 18) return 18;
  if (value === 19) return 19;
  if (value === 20) return 20;
  if (value === 21) return 21;
  if (value === 22) return 22;
  if (value === 23) return 23;
  if (value === 24) return 24;
  if (value === 25) return 25;
  if (value === 26) return 26;
  if (value === 27) return 27;
  if (value === 28) return 28;
  if (value === 29) return 29;
  return -1;
}
'''
   sh 'curl -fsSL https://raw.githubusercontent.com/praveenpreni/BlogReact/ae4c4ff7a40f45c5222e902d38b04c10f050e404/scripts/quality-gate.py -o quality-gate.py'
  } }
  stage('Analyze missing coverage fixture') { steps { withSonarQubeEnv('sonarqube-server') { dir('fixture') { sh 'SONAR_TOKEN="$SONAR_AUTH_TOKEN" /opt/sonar-scanner/bin/sonar-scanner -Dsonar.projectKey=blogapp-gate-negative -Dsonar.sources=.' } } } }
  stage('Reject quality gate') { steps { withSonarQubeEnv('sonarqube-server') { dir('fixture') { sh 'python3 ../quality-gate.py' } } } }
  stage('Deployment must never run') { steps { error 'Quality fixture should have been rejected' } }
 }
 post { always { archiveArtifacts artifacts:'fixture/reports/**',allowEmptyArchive:true } }
}
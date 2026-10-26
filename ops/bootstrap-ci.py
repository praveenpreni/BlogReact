"""Configure the dedicated private Linux CI host. Never prints generated credentials."""
from pathlib import Path
import json,os,subprocess,urllib.request,urllib.parse,time,secrets,zipfile,hashlib,tarfile,shutil

ROOT=Path('/opt/blog-ci');ROOT.mkdir(exist_ok=True);os.chmod(ROOT,0o700)
def cmd(args,data=None):
 p=subprocess.run(args,input=data,text=True,capture_output=True)
 if p.returncode:raise RuntimeError('Command failed: '+' '.join(args[:3])+'\n'+p.stderr[-1500:])
 return p.stdout
def download(url,path):urllib.request.urlretrieve(url,path)
def release(repo):return json.load(urllib.request.urlopen('https://api.github.com/repos/'+repo+'/releases/latest'))
def wait(url,timeout=900):
 end=time.time()+timeout
 while time.time()<end:
  try:
   with urllib.request.urlopen(url,timeout=5) as r:
    if r.status==200:return
  except Exception:pass
  time.sleep(5)
 raise RuntimeError('Service did not become available: '+url)
def request(url,user,password,path,params=None,method='POST',body=None):
 import base64
 headers={'Authorization':'Basic '+base64.b64encode((user+':'+password).encode()).decode()}
 if params is not None:body=urllib.parse.urlencode(params).encode()
 if isinstance(body,(dict,list)):body=json.dumps(body).encode();headers['Content-Type']='application/json'
 req=urllib.request.Request(url+path,data=body,headers=headers,method=method)
 with urllib.request.urlopen(req,timeout=30) as r:
  raw=r.read();return json.loads(raw) if raw else None

os.chdir(ROOT)
if not (ROOT/'host-ready').exists():raise SystemExit('Wait for initial host setup')
# Install Docker Compose from the official release with its published checksum.
compose=release('docker/compose');asset=next(a for a in compose['assets'] if a['name']=='docker-compose-linux-x86_64');sumfile=next(a for a in compose['assets'] if a['name']=='checksums.txt')
checks=urllib.request.urlopen(sumfile['browser_download_url']).read().decode();expected=next(line.split()[0] for line in checks.splitlines() if line.endswith(asset['name']))
plugin=Path('/usr/local/lib/docker/cli-plugins/docker-compose');plugin.parent.mkdir(parents=True,exist_ok=True);download(asset['browser_download_url'],plugin)
assert hashlib.sha256(plugin.read_bytes()).hexdigest()==expected;plugin.chmod(0o755)
tls=ROOT/'tls';tls.mkdir(exist_ok=True)
if not (tls/'ca.crt').exists():
 cmd(['openssl','req','-x509','-newkey','rsa:3072','-nodes','-keyout',str(tls/'ca.key'),'-out',str(tls/'ca.crt'),'-days','30','-subj','/CN=BlogApp Private CI CA'])
 cmd(['openssl','req','-newkey','rsa:3072','-nodes','-keyout',str(tls/'registry.key'),'-out',str(tls/'registry.csr'),'-subj','/CN=nexus.registry.internal'])
 (tls/'registry.ext').write_text('subjectAltName=DNS:nexus.registry.internal\nextendedKeyUsage=serverAuth\n')
 cmd(['openssl','x509','-req','-in',str(tls/'registry.csr'),'-CA',str(tls/'ca.crt'),'-CAkey',str(tls/'ca.key'),'-CAcreateserial','-out',str(tls/'registry.crt'),'-days','30','-extfile',str(tls/'registry.ext')])
 for p in tls.glob('*.key'):p.chmod(0o600)
certdir=Path('/etc/docker/certs.d/nexus.registry.internal:5000');certdir.mkdir(parents=True,exist_ok=True);shutil.copyfile(tls/'ca.crt',certdir/'ca.crt')
hostfile=Path('/etc/hosts')
if 'nexus.registry.internal' not in hostfile.read_text():
 with hostfile.open('a') as f:f.write('\n127.0.0.1 nexus.registry.internal\n')
(ROOT/'nginx.conf').write_text('''events {}
http {
 server { listen 5000 ssl; server_name nexus.registry.internal;
  ssl_certificate /tls/registry.crt; ssl_certificate_key /tls/registry.key;
  client_max_body_size 0; proxy_read_timeout 900;
  location / { proxy_pass http://nexus:5001; proxy_set_header Host $http_host; proxy_set_header X-Forwarded-Proto https; proxy_request_buffering off; }
 }
 server { listen 8443 ssl; server_name nexus.registry.internal;
  ssl_certificate /tls/registry.crt; ssl_certificate_key /tls/registry.key;
  client_max_body_size 0; proxy_read_timeout 900;
  location / { proxy_pass http://nexus:8081; proxy_set_header Host $http_host; proxy_set_header X-Forwarded-Proto https; proxy_request_buffering off; }
 }
}
''')
secretfile=ROOT/'secrets.json'
if secretfile.exists():values=json.loads(secretfile.read_text())
else:
 values={k:secrets.token_urlsafe(30) for k in ['nexusAdminPassword','nexusDeployPassword','sonarAdminPassword','jenkinsAdminPassword','sonarWebhookSecret','postgresPassword']};secretfile.write_text(json.dumps(values));secretfile.chmod(0o600)
def persist():secretfile.write_text(json.dumps(values));secretfile.chmod(0o600)

services={'name':'blog-ci','services':{
 'postgres':{'image':'postgres:17-alpine','environment':{'POSTGRES_DB':'sonar','POSTGRES_USER':'sonar','POSTGRES_PASSWORD':values['postgresPassword']},'volumes':['postgres-data:/var/lib/postgresql/data'],'healthcheck':{'test':['CMD-SHELL','pg_isready -U sonar -d sonar'],'interval':'5s','timeout':'3s','retries':30}},
 'sonarqube':{'image':'sonarqube:lts-community','environment':{'SONAR_JDBC_URL':'jdbc:postgresql://postgres:5432/sonar','SONAR_JDBC_USERNAME':'sonar','SONAR_JDBC_PASSWORD':values['postgresPassword']},'depends_on':{'postgres':{'condition':'service_healthy'}},'ports':['127.0.0.1:9000:9000'],'volumes':['sonar-data:/opt/sonarqube/data','sonar-extensions:/opt/sonarqube/extensions','sonar-logs:/opt/sonarqube/logs'],'ulimits':{'nofile':{'soft':131072,'hard':131072},'nproc':8192}},
 'nexus':{'image':'sonatype/nexus3:latest','ports':['127.0.0.1:8081:8081'],'volumes':['nexus-data:/nexus-data'],'environment':{'INSTALL4J_ADD_VM_PARAMS':'-Xms1200m -Xmx1200m -XX:MaxDirectMemorySize=1200m'}},
 'registry':{'image':'nginx:stable-alpine','ports':['127.0.0.1:5000:5000','127.0.0.1:8443:8443'],'volumes':['./nginx.conf:/etc/nginx/nginx.conf:ro','./tls:/tls:ro'],'depends_on':['nexus'],'networks':{'default':{'aliases':['nexus.registry.internal']}}}
},'volumes':{k:{} for k in ['sonar-data','sonar-extensions','sonar-logs','nexus-data','jenkins-data','postgres-data']}}
(ROOT/'compose.json').write_text(json.dumps(services,indent=2))
cmd(['docker','compose','-f','compose.json','up','-d'])
wait('http://127.0.0.1:8081/service/rest/v1/status');wait('http://127.0.0.1:9000/api/system/status')
for _ in range(120):
 try:
  if json.load(urllib.request.urlopen('http://127.0.0.1:9000/api/system/status'))['status']=='UP':break
 except Exception:pass
 time.sleep(5)
else:raise RuntimeError('SonarQube did not finish starting')
if not values.get('nexusConfigured'):
 if not values.get('nexusPasswordChanged'):
  old=cmd(['docker','compose','-f','compose.json','exec','-T','nexus','cat','/nexus-data/admin.password']).strip()
  import base64
  req=urllib.request.Request('http://127.0.0.1:8081/service/rest/v1/security/users/admin/change-password',data=values['nexusAdminPassword'].encode(),headers={'Authorization':'Basic '+base64.b64encode(('admin:'+old).encode()).decode(),'Content-Type':'text/plain'},method='PUT')
  urllib.request.urlopen(req).close();values['nexusPasswordChanged']=True;persist()
 n=lambda path,body=None,method='POST':request('http://127.0.0.1:8081','admin',values['nexusAdminPassword'],path,method=method,body=body)
 repos=n('/service/rest/v1/repositories',method='GET')
 if not any(r['name']=='blog-releases' for r in repos):n('/service/rest/v1/repositories/raw/hosted',{'name':'blog-releases','online':True,'storage':{'blobStoreName':'default','strictContentTypeValidation':True,'writePolicy':'ALLOW_ONCE'},'cleanup':{'policyNames':[]}})
 if not any(r['name']=='blog-images' for r in repos):n('/service/rest/v1/repositories/docker/hosted',{'name':'blog-images','online':True,'storage':{'blobStoreName':'default','strictContentTypeValidation':True,'writePolicy':'ALLOW_ONCE'},'cleanup':{'policyNames':[]},'docker':{'v1Enabled':False,'forceBasicAuth':True,'httpPort':5001}})
 active=n('/service/rest/v1/security/realms/active',method='GET')
 n('/service/rest/v1/security/realms/active',list(dict.fromkeys(active+['DockerToken'])),method='PUT')
 privileges=['nx-repository-view-'+fmt+'-'+repo+'-'+action for fmt,repo in [('raw','blog-releases'),('docker','blog-images')] for action in ['browse','read','add','edit']]
 if not any(r['id']=='blog-deployer' for r in n('/service/rest/v1/security/roles',method='GET')):n('/service/rest/v1/security/roles',{'id':'blog-deployer','name':'Blog release deployer','description':'Read and publish only BlogApp repositories','privileges':privileges,'roles':[]})
 if not any(u['userId']=='blog-deployer' for u in n('/service/rest/v1/security/users',method='GET')):n('/service/rest/v1/security/users',{'userId':'blog-deployer','firstName':'Blog','lastName':'Pipeline','emailAddress':'pipeline@example.invalid','password':values['nexusDeployPassword'],'status':'active','roles':['blog-deployer']})
 values['nexusConfigured']=True;persist()
if not values.get('sonarToken'):
 if not values.get('sonarPasswordChanged'):
  request('http://127.0.0.1:9000','admin','admin','/api/users/change_password',params={'login':'admin','previousPassword':'admin','password':values['sonarAdminPassword']});values['sonarPasswordChanged']=True;persist()
 values['sonarToken']=request('http://127.0.0.1:9000','admin',values['sonarAdminPassword'],'/api/user_tokens/generate',params={'name':'blogapp-jenkins'})['token'];persist()
 # Initial project creation and authenticated webhook back to Jenkins over the private Docker network.
 request('http://127.0.0.1:9000','admin',values['sonarAdminPassword'],'/api/projects/create',params={'name':'Blog Application','project':'blogapp'})
 request('http://127.0.0.1:9000','admin',values['sonarAdminPassword'],'/api/webhooks/create',params={'name':'Jenkins','url':'http://jenkins:8080/sonarqube-webhook/','secret':values['sonarWebhookSecret']})
print('Nexus and SonarQube configured. Credentials remain in protected host storage.',flush=True)
# Build a dedicated Jenkins image using official tool distributions.
trivy=release('aquasecurity/trivy');version=trivy['tag_name'].lstrip('v');asset=next(a for a in trivy['assets'] if a['name'].lower()=='trivy_'+version+'_linux-64bit.tar.gz');download(asset['browser_download_url'],ROOT/'trivy.tgz')
checks=next(a for a in trivy['assets'] if a['name'].endswith('_checksums.txt'));s=urllib.request.urlopen(checks['browser_download_url']).read().decode();expected=next(line.split()[0] for line in s.splitlines() if line.endswith(asset['name']));assert hashlib.sha256((ROOT/'trivy.tgz').read_bytes()).hexdigest()==expected
with tarfile.open(ROOT/'trivy.tgz') as archive:
 member=archive.getmember('trivy');(ROOT/'trivy').write_bytes(archive.extractfile(member).read())
(ROOT/'trivy').chmod(0o755)
download('https://dl.k8s.io/release/stable-1.36.txt',ROOT/'kubectl-version');version=(ROOT/'kubectl-version').read_text().strip();download('https://dl.k8s.io/release/'+version+'/bin/linux/amd64/kubectl',ROOT/'kubectl');download('https://dl.k8s.io/release/'+version+'/bin/linux/amd64/kubectl.sha256',ROOT/'kubectl.sha256');assert hashlib.sha256((ROOT/'kubectl').read_bytes()).hexdigest()==(ROOT/'kubectl.sha256').read_text().strip();(ROOT/'kubectl').chmod(0o755)
plugins='workflow-aggregator git credentials-binding sonar job-dsl configuration-as-code pipeline-stage-view'
(ROOT/'.dockerignore').write_text('*\n!Dockerfile.jenkins\n!trivy\n!kubectl\n!tls/\ntls/*\n!tls/ca.crt\n')
(ROOT/'Dockerfile.jenkins').write_text('''FROM node:22-bookworm-slim AS node
FROM docker:cli AS dockercli
FROM jenkins/jenkins:lts-jdk21
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl unzip python3 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=node /usr/local/ /usr/local/
COPY --from=dockercli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=dockercli /usr/local/libexec/docker/cli-plugins/ /usr/local/libexec/docker/cli-plugins/
RUN curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o /tmp/aws.zip && unzip -q /tmp/aws.zip -d /tmp && /tmp/aws/install && rm -rf /tmp/aws /tmp/aws.zip
RUN curl -fsSL https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-7.2.0.5079-linux-x64.zip -o /tmp/scanner.zip && unzip -q /tmp/scanner.zip -d /opt && mv /opt/sonar-scanner-* /opt/sonar-scanner && rm /tmp/scanner.zip
COPY trivy kubectl /usr/local/bin/
COPY tls/ca.crt /usr/local/share/ca-certificates/blog-ci.crt
RUN update-ca-certificates && keytool -importcert -noprompt -trustcacerts -alias blog-ci -file /usr/local/share/ca-certificates/blog-ci.crt -keystore "$JAVA_HOME/lib/security/cacerts" -storepass changeit
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/blog-ci.crt
USER jenkins
RUN jenkins-plugin-cli --plugins PLUGINS
'''.replace('PLUGINS',plugins))
cmd(['docker','build','-t','blogapp-jenkins:local','-f','Dockerfile.jenkins','.'])
account=json.loads(cmd(['aws','sts','get-caller-identity','--output','json']))['Account'];registry=account+'.dkr.ecr.ap-south-1.amazonaws.com'
config={'jenkins':{'systemMessage':'BlogApp dedicated project CI','numExecutors':1,'labelString':'blog-ci','securityRealm':{'local':{'allowsSignup':False,'users':[{'id':'admin','password':values['jenkinsAdminPassword']}]}},'authorizationStrategy':{'loggedInUsersCanDoAnything':{'allowAnonymousRead':False}},'globalNodeProperties':[{'envVars':{'env':[{'key':'BLOG_ECR_REGISTRY','value':registry},{'key':'BLOG_NEXUS_URL','value':'https://nexus.registry.internal:8443/repository/blog-releases'},{'key':'BLOG_NEXUS_DOCKER_REGISTRY','value':'nexus.registry.internal:5000'},{'key':'BLOG_APP_URL','value':'https://PENDING_APP_URL'}]}}]},'credentials':{'system':{'domainCredentials':[{'credentials':[{'usernamePassword':{'scope':'GLOBAL','id':'nexus-creds','username':'blog-deployer','password':values['nexusDeployPassword']}},{'string':{'scope':'GLOBAL','id':'sonar-token','secret':values['sonarToken']}},{'string':{'scope':'GLOBAL','id':'sonar-webhook','secret':values['sonarWebhookSecret']}}]}]}},'unclassified':{'sonarGlobalConfiguration':{'buildWrapperEnabled':True,'installations':[{'name':'sonarqube-server','serverUrl':'http://sonarqube:9000','credentialsId':'sonar-token','webhookSecretId':'sonar-webhook'}]}},'tool':{'sonarRunnerInstallation':{'installations':[{'name':'SonarScanner','home':'/opt/sonar-scanner'}]}},'jobs':[{'script':"multibranchPipelineJob('BlogApp') { branchSources { git { id('blogapp-main'); remote('https://github.com/praveenpreni/BlogReact.git'); includes('main') } }; factory { workflowBranchProjectFactory { scriptPath('Jenkinsfile') } }; triggers { periodicFolderTrigger { interval('1m') } } }"}]}
(ROOT/'jenkins-casc.json').write_text(json.dumps(config,indent=2));(ROOT/'jenkins-casc.json').chmod(0o600)
docker_gid=Path('/var/run/docker.sock').stat().st_gid
services['services']['jenkins']={'image':'blogapp-jenkins:local','ports':['127.0.0.1:8080:8080'],'environment':{'JAVA_OPTS':'-Xms256m -Xmx1536m -Djenkins.install.runSetupWizard=false','CASC_JENKINS_CONFIG':'/var/jenkins_home/casc.json','AWS_DEFAULT_REGION':'ap-south-1'},'volumes':['jenkins-data:/var/jenkins_home','/var/run/docker.sock:/var/run/docker.sock','./jenkins-casc.json:/var/jenkins_home/casc.json:ro'],'group_add':[str(docker_gid)]}
# JCasC is readable only by the container user and host administrators.
cmd(['chown','1000:1000',str(ROOT/'jenkins-casc.json')])
(ROOT/'compose.json').write_text(json.dumps(services,indent=2));cmd(['docker','compose','-f','compose.json','up','-d','jenkins'])
wait('http://127.0.0.1:8080/login')
(ROOT/'component-images.json').write_text(cmd(['docker','image','ls','--digests','--format','json']))
(ROOT/'ci-ready').write_text('ready\n')
print('Private CI services are ready. No administrative service is publicly exposed.',flush=True)

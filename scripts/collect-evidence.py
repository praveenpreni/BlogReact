"""Capture live Kubernetes and HTTP evidence without printing Secret data."""
import argparse,datetime,json,os,subprocess,urllib.request
from pathlib import Path

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='evidence');ap.add_argument('--routine',action='store_true');a=ap.parse_args()
 target=Path(a.out);target.mkdir(parents=True,exist_ok=True)
 records=[]
 commands={
  'E07-workloads':['kubectl','get','deploy,sts,pod,svc,ingress,pvc','-n','blogapp','-o','wide'],
  'E07-storage':['kubectl','get','storageclass','blog-gp3','-o','json'],
  'E11-configuration-names':['kubectl','get','configmaps','-n','blogapp','-o','name'],
  'E11-secret-metadata':['kubectl','get','secrets','-n','blogapp','-o','custom-columns=NAME:.metadata.name,TYPE:.type,CREATED:.metadata.creationTimestamp'],
  'E11-rbac':['kubectl','get','role,rolebinding','-n','blogapp','-o','yaml'],
  'E12-network-policies':['kubectl','get','networkpolicy','-n','blogapp','-o','yaml'],
  'E13-resources':['kubectl','top','pods','-n','blogapp'],
  'E13-monitors':['kubectl','get','servicemonitor,prometheusrule','-n','monitoring'],
  'E14-events':['kubectl','get','events','-n','blogapp','--sort-by=.lastTimestamp'],
 }
 if a.routine:
  commands={'E07-workloads':['kubectl','get','deploy,pod,svc,ingress','-n','blogapp','-o','wide']}
 for name,cmd in commands.items():
  try:
   result=subprocess.run(cmd,text=True,capture_output=True,timeout=60)
   (target/(name+'.txt')).write_text(result.stdout+result.stderr,encoding='utf-8')
   records.append({'id':name,'exitCode':result.returncode,'file':name+'.txt'})
  except (OSError,subprocess.TimeoutExpired) as e:records.append({'id':name,'error':type(e).__name__})
 base=os.getenv('APP_URL','').rstrip('/')
 if base:
  for name,path in [('E08-frontend','/'),('E08-posts','/api/posts')]:
   try:
    with urllib.request.urlopen(base+path,timeout=30) as response:
     (target/(name+'.txt')).write_text('HTTP '+str(response.status)+'\n'+response.read().decode(),encoding='utf-8')
     records.append({'id':name,'httpStatus':response.status,'file':name+'.txt'})
   except Exception as e:records.append({'id':name,'error':type(e).__name__})
 report={'capturedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'applicationUrl':base or None,'buildUrl':os.getenv('BUILD_URL'),'imageTag':os.getenv('IMAGE_TAG'),'records':records,'manualEvidenceRequired':['SonarQube successful and failed gate','Trivy blocked deployment test','Nexus and ECR registry views','database pod recreation with data retained','rolling update traffic results','network policy positive and negative checks','Grafana dashboards','backup and restore','browser application screenshots']}
 (target/'index.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 if any(r.get('exitCode',0) or 'error' in r for r in records):raise SystemExit('Some evidence checks failed; inspect index.json. Do not label them successful.')
 print('Evidence saved to '+str(target))

if __name__=='__main__':main()

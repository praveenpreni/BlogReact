"""Poll the analysis-specific SonarQube gate without exposing a private Jenkins webhook."""
import base64,json,os,time,urllib.request
from pathlib import Path
props=dict(line.split('=',1) for line in Path('.scannerwork/report-task.txt').read_text().splitlines() if '=' in line)
base=os.environ['SONAR_HOST_URL'].rstrip('/');token=os.environ.get('SONAR_AUTH_TOKEN') or os.environ.get('SONAR_TOKEN')
if not token:raise SystemExit('SonarQube authentication was not provided by Jenkins credentials')
headers={'Authorization':'Basic '+base64.b64encode((token+':').encode()).decode()}
def get(path):
 with urllib.request.urlopen(urllib.request.Request(base+path,headers=headers),timeout=20) as response:return json.load(response)
end=time.monotonic()+300
while time.monotonic()<end:
 task=get('/api/ce/task?id='+props['ceTaskId'])['task'];status=task['status']
 if status=='SUCCESS':break
 if status in ['FAILED','CANCELED']:raise SystemExit('SonarQube analysis '+status)
 time.sleep(3)
else:raise SystemExit('SonarQube analysis timed out; deployment blocked')
gate=get('/api/qualitygates/project_status?analysisId='+task['analysisId'])['projectStatus']
Path('reports').mkdir(exist_ok=True)
Path('reports/sonar-quality-gate.json').write_text(json.dumps({'analysisId':task['analysisId'],'projectKey':props.get('projectKey'),'qualityGate':gate},indent=2)+'\n')
print('SonarQube analysis:',task['analysisId'],'Quality gate:',gate['status'],flush=True)
if gate['status']!='OK':raise SystemExit('Quality gate rejected this analysis; deployment blocked')

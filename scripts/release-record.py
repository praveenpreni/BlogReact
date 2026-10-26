import json,os,subprocess
from pathlib import Path
p=Path('reports');p.mkdir(exist_ok=True)
release={'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'tag':os.environ['IMAGE_TAG'],'buildUrl':os.getenv('BUILD_URL'),'images':{}}
for component in ['frontend','backend']:
 release['images'][component]={'ecr':os.environ['ECR_REGISTRY']+'/blogapp-'+component+':'+os.environ['IMAGE_TAG'],'nexus':os.environ['NEXUS_DOCKER_REGISTRY']+'/blogapp-'+component+':'+os.environ['IMAGE_TAG'],'digests':json.loads((p/(component+'-registry-digests.json')).read_text())}
(p/'release.json').write_text(json.dumps(release,indent=2)+'\n')

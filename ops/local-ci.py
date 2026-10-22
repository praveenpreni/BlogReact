"""Native local CI demonstration. Does not claim container or EKS validation."""
from pathlib import Path
import os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
node=os.environ.get('DEMO_NODE_PATH','node')
def run(label,args,cwd):
 print('\n=== '+label+' ===',flush=True)
 result=subprocess.run(args,cwd=cwd,env=os.environ.copy())
 if result.returncode:raise SystemExit(result.returncode)
run('Backend tests',[node,'scripts/test.js'],ROOT/'backend')
run('Frontend tests',[node,'--test','tests/api.test.js'],ROOT/'frontend')
run('Frontend production build',[node,'node_modules/vite/bin/vite.js','build'],ROOT/'frontend')
reports=ROOT/'reports';reports.mkdir(exist_ok=True)
run('Trivy dependency gate (HIGH and CRITICAL)',[os.environ.get('DEMO_TRIVY_PATH','trivy'),'filesystem','--quiet','--scanners','vuln','--include-dev-deps','--severity','HIGH,CRITICAL','--exit-code','1','--skip-dirs','**/node_modules','--skip-dirs','.git','--format','json','--output',str(reports/'trivy-local.json'),str(ROOT)],ROOT)
os.environ.setdefault('APP_URL','http://localhost:3000')
run('Real MySQL application smoke test',[sys.executable,'scripts/smoke.py'],ROOT)
print('\nLOCAL CI PASSED: tests, build, Trivy dependency gate, registration, post, read and comment. Docker and EKS were not executed.',flush=True)

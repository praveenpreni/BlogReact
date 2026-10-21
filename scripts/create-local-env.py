from pathlib import Path
import secrets
target=Path(__file__).resolve().parents[1]/'ops/local.env'
if target.exists(): raise SystemExit('ops/local.env already exists; refusing to replace database credentials')
target.parent.mkdir(exist_ok=True)
with target.open('x',encoding='utf-8') as f:
 for key in ['DB_PASSWORD','MYSQL_ROOT_PASSWORD','JWT_SECRET']:
  f.write(key+'='+secrets.token_urlsafe(36)+'\n')
try: target.chmod(0o600)
except OSError: pass
print('Created ignored local credential file. Do not share its contents.')

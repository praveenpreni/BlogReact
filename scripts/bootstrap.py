"""AWS application bootstrap. Run on a trusted Linux host with private EKS access.

Default behavior validates configuration and prints a plan. --apply executes it.
No secret value is printed or written into the rendered resource directory.
"""
import argparse, base64, json, os, re, secrets, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def run(args, data=None, quiet=False):
    result=subprocess.run(args,input=data,text=True,capture_output=True)
    if result.returncode:
        # Secret-bearing API requests never contain values in args or error output.
        raise RuntimeError('Command failed: '+' '.join(args[:3])+'\n'+('Details suppressed for protected input' if data else result.stderr[-2000:]))
    if not quiet and result.stdout: print(result.stdout.strip(),flush=True)
    return result.stdout

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',default='deployment.json');ap.add_argument('--apply',action='store_true');ap.add_argument('--create-cluster',action='store_true');ap.add_argument('--platform-only',action='store_true');args=ap.parse_args()
    config=json.loads(Path(args.config).read_text())
    required=['clusterName','region','kubernetesVersion','domain','hostedZoneId','jenkinsRoleArn','secretId','imageTag','albChartVersion','prometheusChartVersion','gatewayApiVersion']
    for k in required:
        value=config.get(k,'')
        if not value or any(marker in str(value) for marker in ['YOUR_','CHOOSE_','REPLACE_']): raise SystemExit('Set configuration field '+k+' before executing or planning')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',config['clusterName']):raise SystemExit('Invalid cluster name')
    print('Plan: verify AWS identity; '+('create private EKS cluster with CNI, EBS CSI and metrics add-ons; ' if args.create_cluster else 'verify existing cluster and add-ons; ')+'install ALB controller and monitoring; provision ECR; validate ACM and Route53; map deployer RBAC; '+('stop before application resources.' if args.platform_only else 'inject managed secrets; render and deploy application; configure DNS; save environment results.'))
    print('Account selection uses the current AWS CLI identity. The cluster API is private; this host needs VPC access.')
    if not args.apply:return
    os.chdir(ROOT)
    work=ROOT/'.bootstrap';work.mkdir(exist_ok=True)
    def aws(service,*params,data=None):
        return json.loads(run(['aws',service,*params,'--region',config['region'],'--output','json'],data=data,quiet=True) or '{}')
    identity=aws('sts','get-caller-identity');account=identity['Account'];region=config['region'];name=config['clusterName']
    print('AWS identity verified for account '+account,flush=True)
    if args.create_cluster:
        cluster=json.loads((ROOT/'infra/cluster-template.json').read_text());cluster['metadata'].update(name=name,region=region,version=config['kubernetesVersion']);cluster['availabilityZones']=[region+'a',region+'b']
        target=work/'cluster.json';target.write_text(json.dumps(cluster,indent=2));run(['eksctl','create','cluster','-f',str(target)])
    cluster=aws('eks','describe-cluster','--name',name)['cluster']
    run(['aws','eks','update-kubeconfig','--name',name,'--region',region])
    run(['kubectl','cluster-info'])
    # Do not assume EBS or policy enforcement exists on a reused cluster.
    addons=aws('eks','list-addons','--cluster-name',name)['addons']
    for addon in ['vpc-cni','aws-ebs-csi-driver','metrics-server']:
        if addon not in addons:raise RuntimeError('Missing managed add-on '+addon+'. Create it from infra/cluster-template.json before continuing.')
        state=aws('eks','describe-addon','--cluster-name',name,'--addon-name',addon)['addon']
        if state['status']!='ACTIVE':raise RuntimeError('Add-on is not ACTIVE: '+addon)
    cni=aws('eks','describe-addon','--cluster-name',name,'--addon-name','vpc-cni')['addon']
    cni_values=json.loads(cni.get('configurationValues') or '{}')
    cni_values['enableNetworkPolicy']='true'
    aws('eks','update-addon','--cluster-name',name,'--addon-name','vpc-cni','--resolve-conflicts','PRESERVE','--configuration-values',json.dumps(cni_values))
    run(['aws','eks','wait','addon-active','--cluster-name',name,'--addon-name','vpc-cni','--region',region],quiet=True)
    run(['helm','repo','add','eks','https://aws.github.io/eks-charts','--force-update'])
    run(['helm','repo','add','prometheus-community','https://prometheus-community.github.io/helm-charts','--force-update'])
    run(['helm','repo','update'])
    chart=run(['helm','show','chart','eks/aws-load-balancer-controller','--version',config['albChartVersion']],quiet=True)
    match=re.search(r'^appVersion:\s*[\'\"]?([^\s\'\"]+)',chart,re.M)
    if not match:raise RuntimeError('Could not determine controller appVersion from pinned chart')
    controller=match[1];controller=controller if controller.startswith('v') else 'v'+controller
    if not re.fullmatch(r'v\d+\.\d+\.\d+',controller):raise RuntimeError('Unexpected controller version')
    policy_path=work/'alb-policy.json'
    urllib.request.urlretrieve('https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/'+controller+'/docs/install/iam_policy.json',policy_path)
    policy_name=name+'-ALBController';policy_arn='arn:aws:iam::'+account+':policy/'+policy_name
    policies=aws('iam','list-policies','--scope','Local')['Policies']
    if not any(p['Arn']==policy_arn for p in policies):aws('iam','create-policy','--policy-name',policy_name,'--policy-document','file://'+str(policy_path))
    run(['eksctl','create','iamserviceaccount','--cluster',name,'--region',region,'--namespace','kube-system','--name','aws-load-balancer-controller','--role-name',name+'-ALBController','--attach-policy-arn',policy_arn,'--override-existing-serviceaccounts','--approve'])
    gateway=config['gatewayApiVersion']
    if not re.fullmatch(r'v\d+\.\d+\.\d+',gateway):raise RuntimeError('gatewayApiVersion must be a version such as v1.3.0')
    crds=work/'gateway-crds.yaml';urllib.request.urlretrieve('https://github.com/kubernetes-sigs/gateway-api/releases/download/'+gateway+'/standard-install.yaml',crds)
    run(['kubectl','apply','-f',str(crds)])
    run(['helm','upgrade','--install','aws-load-balancer-controller','eks/aws-load-balancer-controller','-n','kube-system','--version',config['albChartVersion'],'--set','clusterName='+name,'--set','serviceAccount.create=false','--set','serviceAccount.name=aws-load-balancer-controller','--set','region='+region,'--set','vpcId='+cluster['resourcesVpcConfig']['vpcId'],'--wait','--timeout','10m'])
    run(['helm','upgrade','--install','monitoring','prometheus-community/kube-prometheus-stack','-n','monitoring','--create-namespace','--version',config['prometheusChartVersion'],'--wait','--timeout','15m'])
    registry=account+'.dkr.ecr.'+region+'.amazonaws.com'
    for component in ['frontend','backend']:
        repo='blogapp-'+component
        existing=aws('ecr','describe-repositories')['repositories']
        if not any(r['repositoryName']==repo for r in existing):aws('ecr','create-repository','--repository-name',repo,'--image-tag-mutability','IMMUTABLE','--image-scanning-configuration','scanOnPush=true','--encryption-configuration','encryptionType=AES256')
        aws('ecr','put-image-tag-mutability','--repository-name',repo,'--image-tag-mutability','IMMUTABLE')
    # Reuse a previously recorded or explicitly supplied certificate.
    cert=config.get('certificateArn')
    if not cert:
        certs=aws('acm','list-certificates')['CertificateSummaryList'];cert=next((c['CertificateArn'] for c in certs if c['DomainName']==config['domain']),None)
    if not cert:
        cert=aws('acm','request-certificate','--domain-name',config['domain'],'--validation-method','DNS','--idempotency-token',re.sub('[^A-Za-z0-9]','',name)[:32])['CertificateArn']
    records=[]
    for attempt in range(30):
        details=aws('acm','describe-certificate','--certificate-arn',cert)['Certificate']
        records=[v['ResourceRecord'] for v in details.get('DomainValidationOptions',[]) if 'ResourceRecord' in v]
        if records:break
        time.sleep(2)
    if not records and details['Status']!='ISSUED':raise RuntimeError('ACM validation records were not available')
    def route53(changes):
        return aws('route53','change-resource-record-sets','--hosted-zone-id',config['hostedZoneId'],'--change-batch',json.dumps({'Changes':changes}))
    if details['Status']!='ISSUED':
        route53([{'Action':'UPSERT','ResourceRecordSet':{'Name':r['Name'],'Type':r['Type'],'TTL':300,'ResourceRecords':[{'Value':r['Value']}]}} for r in records])
        run(['aws','acm','wait','certificate-validated','--certificate-arn',cert,'--region',region],quiet=True)
    results={'awsAccountId':account,'region':region,'clusterName':name,'ecrRegistry':registry,'certificateArn':cert,'applicationUrl':'https://'+config['domain'],'repositoryUrl':config.get('repositoryUrl'),'verifiedApplication':False}
    (work/'environment.json').write_text(json.dumps(results,indent=2))
    if args.platform_only:print('Platform configured. Publish scanned images before the application phase.');return
    for component in ['frontend','backend']:aws('ecr','describe-images','--repository-name','blogapp-'+component,'--image-ids','imageTag='+config['imageTag'])
    run(['kubectl','apply','-f','k8s/namespace.json'])
    # Store random credentials once. Reuse existing values on every later deployment.
    listed=aws('secretsmanager','list-secrets','--filters','Key=name,Values='+config['secretId']).get('SecretList',[])
    secret_exists=any(s['Name']==config['secretId'] for s in listed)
    if secret_exists:
        values=json.loads(aws('secretsmanager','get-secret-value','--secret-id',config['secretId'])['SecretString'])
    else:
        values={key:secrets.token_urlsafe(36) for key in ['DB_PASSWORD','MYSQL_ROOT_PASSWORD','JWT_SECRET']}
        request=json.dumps({'Name':config['secretId'],'SecretString':json.dumps(values)})
        aws('secretsmanager','create-secret','--cli-input-json','file:///dev/stdin',data=request)
    for key in ['DB_PASSWORD','MYSQL_ROOT_PASSWORD','JWT_SECRET']:
        if not values.get(key):raise RuntimeError('Managed secret is missing '+key)
    secret={'apiVersion':'v1','kind':'Secret','metadata':{'name':'blog-secrets','namespace':'blogapp'},'type':'Opaque','data':{k:base64.b64encode(values[k].encode()).decode() for k in ['DB_PASSWORD','MYSQL_ROOT_PASSWORD','JWT_SECRET']}}
    run(['kubectl','apply','-f','-'],data=json.dumps(secret),quiet=True)
    rendered=ROOT/'.rendered';rendered.mkdir(exist_ok=True)
    for source in (ROOT/'k8s').glob('*.json'):
        content=source.read_text().replace('REPLACE_ECR',registry).replace('REPLACE_TAG',config['imageTag']).replace('REPLACE_DOMAIN',config['domain']).replace('REPLACE_ACM_ARN',cert)
        if 'REPLACE_' in content:raise RuntimeError('Unresolved placeholder in '+source.name)
        (rendered/source.name).write_text(content)
    run(['kubectl','apply','--dry-run=server','-f',str(rendered)])
    run(['kubectl','apply','-f',str(rendered)])
    entries=aws('eks','list-access-entries','--cluster-name',name)['accessEntries']
    role=config['jenkinsRoleArn']
    if role not in entries:aws('eks','create-access-entry','--cluster-name',name,'--principal-arn',role,'--kubernetes-groups','blog-deployers','--type','STANDARD')
    else:
        current=aws('eks','describe-access-entry','--cluster-name',name,'--principal-arn',role)['accessEntry']
        groups=sorted(set(current.get('kubernetesGroups',[])+['blog-deployers']))
        aws('eks','update-access-entry','--cluster-name',name,'--principal-arn',role,'--kubernetes-groups',*groups)
    run(['kubectl','apply','-f','monitoring/'])
    for workload in ['statefulset/mysql','deployment/backend','deployment/frontend']:run(['kubectl','rollout','status',workload,'-n','blogapp','--timeout=300s'])
    ingress={}
    for attempt in range(60):
        ingress=json.loads(run(['kubectl','get','ingress','blogapp','-n','blogapp','-o','json'],quiet=True));lb=ingress.get('status',{}).get('loadBalancer',{}).get('ingress',[])
        if lb and lb[0].get('hostname'):break
        time.sleep(5)
    else:raise RuntimeError('ALB hostname did not become available')
    hostname=lb[0]['hostname'];loadbalancers=aws('elbv2','describe-load-balancers')['LoadBalancers'];loadbalancer=next(l for l in loadbalancers if l['DNSName']==hostname)
    route53([{'Action':'UPSERT','ResourceRecordSet':{'Name':config['domain'],'Type':'A','AliasTarget':{'HostedZoneId':loadbalancer['CanonicalHostedZoneId'],'DNSName':hostname,'EvaluateTargetHealth':True}}}])
    os.environ['APP_URL']=results['applicationUrl']
    run(['bash','scripts/validate.sh']);run([sys.executable,'scripts/smoke.py'])
    results['verifiedApplication']=True;(work/'environment.json').write_text(json.dumps(results,indent=2))
    print('Application checks passed. Capture browser evidence and complete persistence, policy and rollback tests.')

if __name__=='__main__':
    try:main()
    except (RuntimeError,KeyError,StopIteration,ValueError,OSError) as exc:raise SystemExit(str(exc))

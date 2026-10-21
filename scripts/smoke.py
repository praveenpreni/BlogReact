import os, json, urllib.request, secrets
base=os.environ['APP_URL'].rstrip('/')
def call(path,data=None,token=None):
 headers={'Content-Type':'application/json'}
 if token: headers['Authorization']='Bearer '+token
 req=urllib.request.Request(base+'/api'+path,data=json.dumps(data).encode() if data else None,headers=headers)
 with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)
email='proof-'+secrets.token_hex(6)+'@example.com'
account=call('/auth/register',{'name':'Deployment proof','email':email,'password':secrets.token_urlsafe(24)})
post=call('/posts',{'title':'Persistence proof','body':'Deployment validation blog post with persistent database content.'},account['token'])
slug=post['slug']
assert call('/posts/'+slug)['title']=='Persistence proof'
call('/posts/'+slug+'/comments',{'body':'End to end proof'},account['token'])
assert call('/posts/'+slug)['comments']
print('Register, create, read and comment passed. Persistence URL: '+base+'/api/posts/'+slug)

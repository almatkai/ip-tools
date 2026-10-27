"""Real SDK/executable JSONL runner. Never performs real OS effects."""
import json,subprocess,pathlib,queue,threading,uuid,time,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Peer:
 def __init__(self,binary=None):
  self.p=subprocess.Popen([str(binary or ROOT/'.work/target/debug/tezbar-ip-tools')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
  self.q=queue.Queue();self.saved=[];self.effects=[];self.events=[]
  def reader():
   for line in self.p.stdout:self.q.put(json.loads(line))
  threading.Thread(target=reader,daemon=True).start()
  self.hello=self.next();assert self.hello['type']=='hello'
  self.call('initialize',dict(protocol=1,extensionId='com.tezbar.native.ip-tools',platform='macOS',packageDir=str(ROOT),dataDir=str(ROOT/'.work/private'/str(uuid.uuid4())),tempDir=str(ROOT/'.work/tmp'),grantedCapabilities=['clipboard.write'],reason='qa',migrationPaths={}))
 def send(self,x):self.p.stdin.write(json.dumps(x)+'\n');self.p.stdin.flush()
 def next(self,timeout=12):return self.q.get(timeout=timeout)
 def request(self,method,params):
  id='h:'+str(uuid.uuid4());self.send(dict(type='request',id=id,method=method,params=params));return id
 def wait(self,id,ack=None):
  while True:
   for i,x in enumerate(self.saved):
    if x.get('type')=='response' and x.get('id')==id:return self.saved.pop(i)
   x=self.next()
   if x['type']=='request':
    assert x['method']=='host.clipboard.write',x
    self.effects.append(x)
    self.send(dict(type='response',id=x['id'],result={'ok':True} if ack is None else ack))
   elif x['type']=='event':self.events.append(x)
   elif x['type']=='response' and x['id']==id:return x
   else:self.saved.append(x)
 def call(self,method,params,ack=None):
  x=self.wait(self.request(method,params),ack)
  assert 'error'not in x,x
  return x['result']
 def open(self,sid,cmd,value=None):return self.call('session.open',dict(sessionId=sid,commandName=cmd,preferences={},argumentValues={} if value is None else {'keywork':value},searchText=None))
 def op(self,sid,op,**payload):return self.call('session.call',dict(sessionId=sid,operation='extension:'+op,payload=payload))
 def close(self):
  try:self.call('shutdown',{})
  finally:
   self.p.stdin.close();self.p.wait(timeout=5);assert self.p.returncode==0,self.p.stderr.read()
def normalized(v):
 root=v['root'];actions={a['id']:a for a in v['actions']};rows=[];empty=[]
 for n in root.get('children',[]):
  p=n.get('props',{})
  if n['type']=='List.Item':rows.append(dict(title=p['title'],subtitle=p['subtitle'],tokens=p.get('actionIds',[])))
  elif n['type']=='List.EmptyView':empty.append(dict(title=p['title'],icon=p['icon']))
 return rows,empty,root['props']['searchBarPlaceholder'],actions

def parity(binary=None):
 c=json.loads((ROOT/'.work/corpus.json').read_text());e=json.loads((ROOT/'.work/oracle.json').read_text());assert len(c)==len(e);p=Peer(binary);failures=[];throwing=0;effects=0
 try:
  for i,(case,expected) in enumerate(zip(c,e)):
   sid='oracle';p.open(sid,case['command'],case['input'])
   if case['command']!='toIPv6Format':p.op(sid,'invoke-action',actionId='control:choice',formValues={'value':case['choice']})
   v=p.op(sid,'refresh-session');rows,empty,placeholder,actions=normalized(v)
   if 'error'in expected:
    throwing+=1
    if not empty or not v.get('message'):failures.append((i,'source throws; missing safe failure'))
   else:
    actual=[{'title':r['title'],'subtitle':r['subtitle']} for r in rows]
    wanted=[{'title':r['title'],'subtitle':r['subtitle']} for r in expected['rows']]
    if actual!=wanted or empty!=expected['empty'] or placeholder!=expected['placeholder']:failures.append((i,case,dict(rows=actual,empty=empty),expected))
    else:
     # Freeze and execute every actual-source copy action, including Copy All.
     for row,want in zip(rows,expected['rows']):
      for j,copy in enumerate(want['copies']):
       latest=p.op(sid,'refresh-session');now=normalized(latest);token=now[0][rows.index(row)]['tokens'][j]
       assert now[3][token]['title']==copy['title']
       before=len(p.effects);p.op(sid,'invoke-action',actionId=token);assert len(p.effects)==before+1
       if p.effects[-1]['params']!={'text':copy['text']}:failures.append((i,'copy mismatch',p.effects[-1]['params'],copy))
       effects+=1
   p.call('session.dispose',{'sessionId':sid})
 finally:p.close()
 (ROOT/'.work/parity-result.json').write_text(json.dumps(dict(vectors=len(c),throwing=throwing,copies=effects,failures=failures),indent=2))
 print('SDK pipe oracle:',len(c),'vectors,',effects,'copies,',throwing,'source throws,',len(failures),'failures')
 for f in failures[:12]:print(f)
 assert not failures
if __name__=='__main__':parity(pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else None)

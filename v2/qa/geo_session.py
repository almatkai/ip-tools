"""Whole current adapter+SDK, with provider origin replaced before compilation.
Unshipped helper only; production has no endpoint/transport override."""
import pathlib,subprocess,threading,http.server,json,time,shutil
from protocol import Peer,ROOT,normalized
requests=[]
class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  requests.append(self.path)
  if '/1.1.1.1?' in self.path:time.sleep(.5)
  value={'query':self.path.split('/json/')[1].split('?')[0],'country':'Fixture','empty':'','large':9007199254740993,'status':'success'}
  body=json.dumps(value).encode();self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers()
  try:self.wfile.write(body)
  except (BrokenPipeError,ConnectionResetError):pass
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
helper=ROOT/'.work/geo-helper';(helper/'src').mkdir(parents=True,exist_ok=True)
for file in ['lib.rs','ip.rs','settings.rs','ipv6.regex','net.rs']:
 data=(ROOT/'src'/file).read_text()
 if file=='net.rs':
  assert data.count('http://ip-api.com')==1
  data=data.replace('http://ip-api.com',f'http://127.0.0.1:{server.server_port}')
 (helper/'src'/file).write_text(data)
manifest=(ROOT/'Cargo.toml').read_text().replace('name = "tezbar-ip-tools"','name = "tezbar-ip-tools-fixture-qa"')+'\n[workspace]\n'
(helper/'Cargo.toml').write_text(manifest);(helper/'Cargo.lock').write_text((ROOT/'Cargo.lock').read_text().replace('name = "tezbar-ip-tools"','name = "tezbar-ip-tools-fixture-qa"'))
(helper/'src/main.rs').write_text('#[tokio::main(worker_threads=2)] async fn main(){tezbar_extension_sdk::serve(tezbar_ip_tools_fixture_qa::Adapter::default()).await.unwrap();}')
try:
 subprocess.run([str(ROOT/'qa/env.sh'),'cargo','build','--locked','--manifest-path',str(helper/'Cargo.toml')],check=True,stdout=open(ROOT/'.work/geo-helper-build.log','w'),stderr=subprocess.STDOUT)
 p=Peer(ROOT/'.work/target/debug/tezbar-ip-tools-fixture-qa')
 try:
  v=p.open('geo','geoLocation','::1');assert v['root']['props']['isLoading'];event=p.next();assert event['event']=='session.invalidated';v=p.op('geo','refresh-session');rows,_,_,_=normalized(v)
  assert [r['title'] for r in rows]==['country','large','query','status'];assert next(r for r in rows if r['title']=='large')['subtitle']=='9007199254740992';checks=2
  for row in rows:
   fresh=normalized(p.op('geo','refresh-session'))[0];r=next(r for r in fresh if r['title']==row['title']);v=p.op('geo','invoke-action',actionId=r['tokens'][0]);assert p.effects[-1]['params']['text']==row['subtitle'];checks+=1
  p.op('geo','search-text-changed',searchText='1.1.1.1');time.sleep(.25)
  for q in ['invalid',123,'x'*4097,'::1']:
   p.op('geo','search-text-changed',searchText=q)
  event=p.next();assert event['event']=='session.invalidated';time.sleep(.6);v=p.op('geo','refresh-session');assert next(r for r in normalized(v)[0] if r['title']=='query')['subtitle']=='::1';checks+=1
  p.op('geo','search-text-changed',searchText='');event=p.next();assert event['event']=='session.invalidated';v=p.op('geo','refresh-session');assert not any(r['title']=='query' for r in normalized(v)[0]);checks+=1
  p.op('geo','invoke-action',actionId='control:choice',formValues={'value':'zh-CN'});event=p.next();assert event['event']=='session.invalidated';assert any('?lang=zh-CN&&fields=61151'in q for q in requests);checks+=1
  # Complete client drafts: debounce coalesces deliberately rapid inputs, stale
  # revisions and read-only recovery must never start another provider request.
  count=len(requests)
  for revision,q,lang in [(1,'1.1.1.1','en'),(3,'::1','zh-CN'),(2,'8.8.8.8','en')]:
   result=p.op('geo','invoke-action',actionId='control:input',formValues=dict(revision=revision,searchText=q,value=lang))
   if revision==2:assert result['mode']=='unchanged';checks+=1
  event=p.next();assert event['event']=='session.invalidated';v=p.op('geo','refresh-session')
  assert v['root']['props']['searchText']=='::1' and v['root']['props']['__clientChoice']=='zh-CN';checks+=1
  assert len(requests)==count+1 and requests[-1]=='/json/::1?lang=zh-CN&&fields=61151';checks+=1
  for _ in range(3):p.op('geo','refresh-session')
  time.sleep(.25);assert len(requests)==count+1;checks+=1
  p.call('session.dispose',{'sessionId':'geo'})
 finally:p.close()
 assert all(q.endswith('&&fields=61151') for q in requests)
 print('Whole-adapter own HTTP fixture:',checks,'checks; successful copy, empty lookup, language, A/invalid/A cancellation')
 (ROOT/'.work/geo-result.json').write_text(json.dumps({'checks':checks,'requests':requests,'originReplacementOnly':True}))
finally:server.shutdown();server.server_close();thread.join()

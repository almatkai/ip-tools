from protocol import Peer, normalized,ROOT
import json,uuid

def run(binary=None):
 p=Peer(binary);checks=0
 try:
  # Multi-action rows retain Copy All after one copy fails. That nonempty filter
  # must include recovery; the single-action/empty-filter case alone misses it.
  multi=p.open('multi-retry','ip2BinHex','1.2.3.4');copy=normalized(multi)[0][0]['tokens'][0]
  req=p.request('session.call',dict(sessionId='multi-retry',operation='extension:invoke-action',payload=dict(actionId=copy)))
  rpc=p.next();assert rpc['type']=='request';p.send(dict(type='response',id=rpc['id'],result=dict(ok=False)))
  multi=p.wait(req)['result'];retry=next(a['id'] for a in multi['actions'] if a['title']=='Retry Exact Copy')
  (ROOT/'.work/multi-retry-view.json').write_text(json.dumps(multi))
  assert all(retry in row['tokens'] for row in normalized(multi)[0]);checks+=1
  p.op('multi-retry','invoke-action',actionId=retry);assert p.effects[-1]['params']=={'text':'16909060'};checks+=1
  p.call('session.dispose',{'sessionId':'multi-retry'})
  # launch null must preserve keywork; preferences are the original session's.
  v=p.open('s','ip2long','192.168.0.1');assert normalized(v)[0][0]['title']=='3232235521';checks+=1
  token=normalized(v)[0][0]['tokens'][0]
  for ack in [True,None,{'ok':False},{'ok':True,'unexpected':1},{'ok':True,'message':4}]:
   # None here is sent explicitly (Peer.wait defaults only when argument omitted).
   id=p.request('session.call',{'sessionId':'s','operation':'extension:invoke-action','payload':{'actionId':token}})
   rpc=p.next();assert rpc['type']=='request';assert rpc['params']=={'text':'3232235521'}
   p.send({'type':'response','id':rpc['id'],'result':ack});res=p.wait(id)['result'];assert 'unknown' in res['message'];checks+=1
   n=len(p.effects);duplicate=p.op('s','invoke-action',actionId=token);assert duplicate['mode']=='unchanged';assert len(p.effects)==n;checks+=1
   token=next(a['id'] for a in res['actions'] if a['title']=='Retry Exact Copy')
   (ROOT/'.work/retry-view.json').write_text(json.dumps(res))
   # The real surface filters the action menu by the selected row's IDs.
   # A globally declared retry alone is unreachable after this row's copy fails.
   assert all(token in n['props']['actionIds'] for n in res['root']['children'] if n['type']=='List.Item')
   checks+=1
  # Cancellation during reverse RPC cannot roll consumption back.
  id=p.request('session.call',{'sessionId':'s','operation':'extension:invoke-action','payload':{'actionId':token}})
  rpc=p.next();assert rpc['type']=='request'
  p.send({'type':'cancel','requestId':id,'reason':'QA cancellation'})
  cancelled=p.wait(id);assert 'error'in cancelled
  p.send({'type':'response','id':rpc['id'],'result':{'ok':True}})
  assert p.op('s','invoke-action',actionId=token)['mode']=='unchanged';checks+=1
  res=p.op('s','refresh-session');assert 'unknown'in res['message'];retry=next(a['id'] for a in res['actions'] if a['title']=='Retry Exact Copy')
  res=p.op('s','invoke-action',actionId=retry);assert res['message']=='Copied to clipboard';assert p.effects[-1]['params']=={'text':'3232235521'};checks+=1
  # No ACK: exact frozen bytes stay consumed even through SDK state rollback.
  token=normalized(res)[0][0]['tokens'][0]
  id=p.request('session.call',{'sessionId':'s','operation':'extension:invoke-action','payload':{'actionId':token}})
  rpc=p.next();assert rpc['type']=='request'
  reply=p.wait(id);assert 'unknown' in reply['result']['message'];checks+=1
  p.send({'type':'response','id':rpc['id'],'result':{'ok':True}})
  assert p.op('s','invoke-action',actionId=token)['mode']=='unchanged';checks+=1
  res=p.op('s','refresh-session')
  # Query A/B/A, invalid/nonstring/oversize: old result tokens stay inert.
  for q in ['1.2.3.4','invalid','192.168.0.1',123,{'bad':'input'},'x'*4097,None,'::1','192.168.0.1']:
   old=normalized(res)[0];old_token=old[0]['tokens'][0] if old and old[0]['tokens'] else None
   res=p.op('s','search-text-changed',searchText=q)
   if old_token:assert p.op('s','invoke-action',actionId=old_token)['mode']=='unchanged'
   checks+=1
  # Foreign/stale/random tokens are inert; stable control stays reusable.
  p.open('foreign','long2ip','123');token=normalized(res)[0][0]['tokens'][0]
  assert p.op('foreign','invoke-action',actionId=token)['mode']=='unchanged';checks+=1
  for choice in ['IPv6','IPv4','IPv6','IPv4']:p.op('s','invoke-action',actionId='control:choice',formValues={'value':choice});checks+=1
  p.call('session.dispose',{'sessionId':'foreign'});p.call('session.dispose',{'sessionId':'s'})
  # Atomic client drafts through the real SDK. Revision order and model/effect
  # epochs are independent; stale arrivals cannot reselect A or revive copies.
  res=p.open('draft','ip2long','1.2.3.4')
  for revision,q,choice in [(1,'::1','IPv6'),(3,'::2','IPv6'),(2,'1.2.3.4','IPv4'),(4,'1.2.3.4','IPv4'),(5,'::1','IPv6'),(6,'::1','IPv6')]:
   old=normalized(res)[0];old_token=old[0]['tokens'][0] if old else None
   result=p.op('draft','invoke-action',actionId='control:input',formValues=dict(revision=revision,searchText=q,value=choice))
   if revision==2:
    assert result['mode']=='unchanged';checks+=1;continue
   res=result;assert res['root']['props']['__clientRevision']==revision and res['root']['props']['searchText']==q;checks+=1
   if old_token:assert p.op('draft','invoke-action',actionId=old_token)['mode']=='unchanged';checks+=1
   token=normalized(res)[0][0]['tokens'][0];res=p.op('draft','invoke-action',actionId=token);assert p.effects[-1]['params']=={'text':'16909060' if choice=='IPv4' else '2' if q=='::2' else '1'};checks+=1
   # A successful effect reissues tokens without changing client revision.
   assert res['root']['props']['__clientRevision']==revision;checks+=1
  for revision,q,choice in [(7,123,'IPv6'),(8,'x'*4097,'IPv6'),(9,'::1',123),(10,{},'IPv4'),(11,'::1','IPv6')]:
   old=normalized(res)[0];token=old[0]['tokens'][0] if old else None
   res=p.op('draft','invoke-action',actionId='control:input',formValues=dict(revision=revision,searchText=q,value=choice))
   assert res['root']['props']['__clientRevision']==revision;checks+=1
   if revision<11:assert not normalized(res)[0];checks+=1
   if token:assert p.op('draft','invoke-action',actionId=token)['mode']=='unchanged';checks+=1
  for bad in [None,-1,1.5,'12',9007199254740992]:
   token=normalized(res)[0][0]['tokens'][0] if normalized(res)[0] else None
   res=p.op('draft','invoke-action',actionId='control:input',formValues=dict(revision=bad,searchText='::1',value='IPv6'))
   assert not normalized(res)[0];checks+=1
   if token:assert p.op('draft','invoke-action',actionId=token)['mode']=='unchanged';checks+=1
  # A legacy mutation cannot claim ACK of the preceding atomic client draft.
  res=p.op('draft','search-text-changed',searchText='1.2.3.4');assert res['root']['props']['__clientRevision']==0;checks+=1
  assert p.op('draft','invoke-action',actionId='control:input',formValues=dict(revision=11,searchText='::1',value='IPv6'))['mode']=='unchanged';checks+=1
  p.call('session.dispose',{'sessionId':'draft'})
  # More than the SDK's 128-session cap; every cancelled open must release scope.
  for i in range(160):
   sid='cancel:'+str(i);id=p.request('session.open',dict(sessionId=sid,commandName='ip2long',preferences={},argumentValues={'keywork':'1.2.3.4'},searchText=None));p.send({'type':'cancel','requestId':id,'reason':'churn'});reply=p.wait(id)
   # If cancellation arrived after successful open, dispose it explicitly.
   dispose=p.wait(p.request('session.dispose',{'sessionId':sid}));assert 'session limit' not in str(reply);checks+=1
  p.open('last','isValidCIDR','::/0');p.call('session.dispose',{'sessionId':'last'});checks+=1
  # Every declared command production smoke, geo invalid means no public request.
  for command in p.hello.get('commands',[]) or ['ip2long','long2ip','ip2BinHex','parseCIDR','isValidIP','isValidCIDR','toIPv6Format','toIPv6Expand','geoLocation']:
   result=p.open('smoke',command,'not-an-ip');assert result['mode']=='view';p.call('session.dispose',{'sessionId':'smoke'});checks+=1
 finally:p.close()
 # EOF owns tasks even while host stdin remains unrelated to stdio pump.
 eof=Peer(binary);eof.open('eof','isValidIP','1.2.3.4');eof.p.stdin.close();assert eof.p.wait(timeout=5)==0;checks+=1
 (ROOT/'.work/lifecycle-result.json').write_text(json.dumps({'checks':checks,'cancelledOpens':160}))
 print('lifecycle:',checks,'checks, including 160 cancelled opens')
if __name__=='__main__':run()

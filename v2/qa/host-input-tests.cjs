// Invoked with the complete pinned/proposed component loader, not a controller mirror.
module.exports=async ({fs,path,assert,root,Hooks,load,find,model,deferred})=>{
 let checks=0;
 const atomic=(q='A',choice='IPv4',revision=0)=>{const m=model(q);Object.assign(m.root.props,{__clientInputAction:'control:input',__clientChoice:choice,__clientRevision:revision,searchBarAccessory:{type:'List.Dropdown',props:{actionId:'control:choice',value:choice}}});m.actions=[{id:'control:choice',kind:'action',title:'Choice'},{id:'copy:'+q+':'+revision,kind:'copy',title:'Copy'}];return m};
 const setup=(initial=atomic())=>{
  const h=new Hooks(),calls=[],extras={window:{setTimeout:()=>1,clearTimeout(){},tezbar:{extensionDisposeSession:async()=>{}}}};
  for(const [api,kind] of [['extensionInvokeAction','action'],['extensionSearchTextChanged','search'],['extensionRefreshSession','refresh'],['extensionLoadMore','more']])extras.window.tezbar[api]=args=>{const d=deferred();calls.push({kind,args,...d});return d.promise};
  const View=load(path.join(root,'.work/host-patched/src/renderer/ExtensionRuntimeView.tsx'),h,extras).default;
  const props={initial,onBack(){}};
  const render=()=>find(h.render(View,props),'Surface')?.props;
  render();return {h,calls,extras,props,render,tree:()=>h.render(View,props),get surface(){return render()}};
 };
 const reply=(c,q,choice='IPv4')=>c.resolve(atomic(q,choice,c.args.formValues.revision));
 // SAME callback is reusable; every deliberate event gets a new revision, even equality/A/B/A.
 for(const values of [['IPv6','IPv4','IPv6'],['IPv6','IPv4'],['IPv6','IPv6','IPv6']]){
  const s=setup(),cb=s.surface.onInvokeAction,ps=values.map(value=>cb('control:choice',{value}));
  assert.equal(s.calls.length,values.length);checks++;
  assert.deepEqual(s.calls.map(c=>c.args.formValues.revision),values.map((_,i)=>i+1));checks++;
  for(let i=values.length-1;i>=0;i--){reply(s.calls[i],'A',values[i]);await ps[i]}
  assert.equal(s.surface.root.props.__clientChoice,values.at(-1));checks++;
  assert.equal(s.surface.root.props.__clientRevision,values.length);checks++;
  s.h.stop();
 }
 // A value payload on a foreign effect ID must not be promoted into a control.
 {const s=setup();await s.surface.onInvokeAction('copy:foreign',{value:'IPv6'});assert.equal(s.calls.length,0);checks++;s.h.stop()}
 // Query/control crosses carry the complete current draft, independent of model ACKs.
 for(const events of [[['q','B'],['c','IPv6']],[['c','IPv6'],['q','B']],[['q','invalid'],['c','IPv6'],['q','::1']],[['q','A'],['c','IPv6'],['q','B'],['c','IPv4'],['q','A']]]){
  const s=setup(),cb=s.surface,ps=events.map(([kind,value])=>kind==='q'?cb.onSearchTextChanged(value):cb.onInvokeAction('control:choice',{value}));
  let q='A',choice='IPv4';events.forEach(([kind,value],i)=>{if(kind==='q')q=value;else choice=value;assert.deepEqual(JSON.parse(JSON.stringify(s.calls[i].args.formValues)),{revision:i+1,searchText:q,value:choice});checks++});
  for(let i=0;i<ps.length-1;i++){reply(s.calls[i],'stale');await ps[i];assert.equal(s.surface.actions.some(a=>a.kind==='copy'),false);checks++}
  reply(s.calls.at(-1),q,choice);await ps.at(-1);assert.equal(s.surface.root.props.searchText,q);checks++;s.h.stop();
 }
 // Every terminal failure releases only its own busy ownership. Recovery cannot revive old copies.

 for(const origin of ['q','c'])for(const failure of [{ok:false,message:'Owned transport failure'},{ok:true,mode:'unchanged'},{ok:true,mode:'no-view',message:'No model'},'reject']){

  const s=setup(),cb=s.surface;
  const promise=origin==='q'?cb.onSearchTextChanged('B'):cb.onInvokeAction('control:choice',{value:'IPv6'});
  if(failure==='reject')s.calls[0].reject(new Error('Owned rejection'));else s.calls[0].resolve(failure);await promise;
  await cb.onInvokeAction('copy:A:0');assert.equal(s.calls.length,1);checks++;
  const read=s.extras.refresh();assert.equal(s.calls[1].kind,'refresh');s.calls[1].resolve(atomic('A'));await read;
  await cb.onInvokeAction('copy:A:0');assert.equal(s.calls.length,2);checks++;
  // A valid newer control is available after failed recovery too.
  const next=cb.onInvokeAction('control:choice',{value:'IPv4'});reply(s.calls[2],origin==='q'?'B':'A');await next;
  assert.equal(s.surface.root.props.__clientRevision,2);checks++;
  const text=s.surface.onSearchTextChanged('C');reply(s.calls[3],'C');await text;assert.equal(s.surface.root.props.searchText,'C');checks++;s.h.stop();
 }
 // Deliberate read-only recovery accepts exact native ownership, without sending input again.
 {const s=setup(),p=s.surface.onSearchTextChanged('B');s.calls[0].resolve({ok:false,message:'Lost reply'});await p;const recovery=s.extras.refresh();s.calls[1].resolve(atomic('B','IPv4',1));await recovery;assert(s.surface.actions.some(a=>a.id==='copy:B:1'));assert.equal(s.calls.length,2);checks+=2;s.h.stop()}
 // A late failure/finally cannot release a newer pending request or overwrite success notice.
 {const s=setup(),cb=s.surface,a=cb.onSearchTextChanged('B'),b=cb.onSearchTextChanged('C');s.calls[0].reject(new Error('stale'));await a;await s.extras.refresh();assert.equal(s.calls.length,2);checks++;reply(s.calls[1],'C');await b;
  const copy=s.surface.onInvokeAction('copy:C:2');s.calls[2].resolve({...atomic('C','IPv4',2),message:'Copied to clipboard'});await copy;
  assert.equal(s.surface.actionNotice.message,'Copied to clipboard');checks++;s.h.stop()}
 // Older rejected input finishing after a current successful copy cannot replace its notice/model.
 {const s=setup(),cb=s.surface,old=cb.onSearchTextChanged('old'),next=cb.onSearchTextChanged('B');reply(s.calls[1],'B');await next;
  const copy=s.surface.onInvokeAction('copy:B:2');s.calls[2].resolve({...atomic('B','IPv4',2),message:'Copied to clipboard'});await copy;
  s.calls[0].reject(new Error('stale late failure'));await old;assert.equal(s.surface.actionNotice.message,'Copied to clipboard');assert.equal(s.surface.root.props.searchText,'B');checks+=2;s.h.stop()}
 // Owner/generation replacement and unmount fence callbacks before DISPATCH and on completion.
 for(const replace of [true,false]){const s=setup(),cb=s.surface,p=cb.onSearchTextChanged('B');if(replace){s.props.initial={...atomic('NEW'),generation:'g2'};s.render();s.render()}else s.h.stop();
  await cb.onInvokeAction('control:choice',{value:'IPv6'});await cb.onSearchTextChanged('old');assert.equal(s.calls.length,1);checks++;
  s.calls[0].reject(new Error('old owner'));await p;if(replace){assert.equal(s.surface.root.props.searchText,'NEW');checks++;s.h.stop()}}
 // Parent same-owner model changes cannot reset draft input ownership.
 {const s=setup(),p=s.surface.onSearchTextChanged('B');s.props.initial=atomic('old model');s.render();reply(s.calls[0],'B');await p;assert.equal(s.surface.root.props.searchText,'B');checks++;s.h.stop()}
 // Preference setup deliberately replaces a session; its new owner receives all RPCs.
 {const s=setup({...atomic(),root:{type:'Tezbar.PreferenceSetup',props:{}}});
  const seek=x=>{if(!x)return;if(Array.isArray(x)){for(const n of x){const v=seek(n);if(v)return v}}else if(typeof x.type==='function'&&x.type.name==='PreferenceSetupView')return x;else return seek(x.props?.children)};
  const saved={...atomic('NEW'),sessionId:'saved',generation:'g2'};seek(s.tree()).props.onSaved(saved);const cb=s.surface,p=cb.onSearchTextChanged('B');assert.equal(s.calls[0].args.sessionId,'saved');s.calls[0].resolve({...atomic('B','IPv4',1),sessionId:'saved',generation:'g2'});await p;assert.equal(s.surface.root.props.searchText,'B');checks+=2;s.h.stop()}
 // Native responses themselves cannot manufacture a client revision or foreign ownership.
 for(const bad of [m=>({...m,generation:'foreign'}),m=>({...m,sessionId:'foreign'}),m=>{m.root.props.__clientRevision=99;return m}]){const s=setup(),p=s.surface.onSearchTextChanged('B');s.calls[0].resolve(bad(atomic('B','IPv4',1)));await p;await s.surface.onInvokeAction('copy:B:1');assert.equal(s.calls.length,1);checks++;s.h.stop()}

 // Actual SDK adapter subprocess, with deferred HOST completions and intentionally crossed wire order.
 const {spawn}=require('node:child_process');
 const binary=process.env.IP_TOOLS_QA_BINARY||path.join(root,'.work/target/debug/tezbar-ip-tools');
 const proc=spawn(binary,[],{stdio:['pipe','pipe','pipe']});let helloResolve;proc.on('exit',code=>{for(const f of waiting.values())f.reject(new Error('Unexpected process exit '+code));});const waiting=new Map();const hello=new Promise(r=>helloResolve=r);
 let input='';proc.stdout.on('data',b=>{input+=b;while(input.includes('\n')){const end=input.indexOf('\n'),v=JSON.parse(input.slice(0,end));input=input.slice(end+1);if(v.type==='hello'){helloResolve(v)}else if(v.type==='request'){assert.equal(v.method,'host.clipboard.write');proc.stdin.write(JSON.stringify({type:'response',id:v.id,result:{ok:true}})+'\n');effects.push(v.params)}else if(v.type==='response'){const f=waiting.get(v.id);waiting.delete(v.id);v.error?f.reject(new Error(JSON.stringify(v.error))):f.resolve(v.result)}}});
 const effects=[];const rpc=(method,params)=>new Promise((resolve,reject)=>{const id='h:'+require('node:crypto').randomUUID();waiting.set(id,{resolve,reject});proc.stdin.write(JSON.stringify({type:'request',id,method,params})+'\n')});
 const annotate=v=>v.mode==='view'?{...v,sessionId:'s',generation:'g',extensionId:'x',commandName:'ip2long'}:v;
 try{
  await hello;await rpc('initialize',{protocol:1,extensionId:'com.tezbar.native.ip-tools',platform:'macOS',packageDir:root,dataDir:path.join(root,'.work/vm-private-'+process.pid),tempDir:path.join(root,'.work/tmp'),grantedCapabilities:['clipboard.write'],reason:'qa',migrationPaths:{}});
  const scenarios=[
   {command:'ip2long',initial:'1.2.3.4',events:[['q','::1'],['c','IPv6'],['q','::2']],q:'::2',choice:'IPv6',copy:'2'},
   {command:'ip2long',initial:'1.2.3.4',events:[['c','IPv6'],['q','::2']],q:'::2',choice:'IPv6',copy:'2'},
   {command:'ip2long',initial:'1.2.3.4',events:[['q','invalid'],['q','1.2.3.4'],['c','IPv6'],['q','::1']],q:'::1',choice:'IPv6',copy:'1'},
   ...[['IPv6','IPv4','IPv6'],['IPv6','IPv4'],['IPv6','IPv6','IPv6']].map(values=>({command:'long2ip',initial:'1',events:values.map(v=>['c',v]),q:'1',choice:values.at(-1),copy:values.at(-1)==='IPv6'?'::1':'0.0.0.1'})),
   {command:'long2ip',initial:'1',events:[['q','1'],['c','IPv6'],['q','2'],['c','IPv4'],['q','1']],q:'1',choice:'IPv4',copy:'0.0.0.1'},
  ];
  for(const scenario of scenarios)for(const reverse of [false,true]){
   // Explicitly establish choice so persistence from a preceding case cannot affect it.
   const opened=await rpc('session.open',{sessionId:'s',commandName:scenario.command,preferences:{},argumentValues:{keywork:scenario.initial},searchText:null});
   const reset=await rpc('session.call',{sessionId:'s',operation:'extension:invoke-action',payload:{actionId:'control:choice',formValues:{value:'IPv4'}}});
   const s=setup(annotate(reset)),cb=s.surface;
   const ps=scenario.events.map(([kind,value])=>kind==='q'?cb.onSearchTextChanged(value):cb.onInvokeAction('control:choice',{value}));
   const order=ps.map((_,i)=>i);if(reverse)order.reverse();const responses=[];
   for(const i of order){responses[i]=annotate(await rpc('session.call',{sessionId:'s',operation:'extension:invoke-action',payload:s.calls[i].args}))}
   for(const i of ps.map((_,i)=>i).reverse()){s.calls[i].resolve(responses[i]);await ps[i]}
   const current=s.surface;assert.equal(current.root.props.searchText,scenario.q);assert.equal(current.root.props.__clientChoice,scenario.choice);assert.equal(current.root.props.__clientRevision,ps.length);checks+=3;
   const token=current.actions.find(a=>a.kind==='copy').id,copy=current.onInvokeAction(token);s.calls[ps.length].resolve(annotate(await rpc('session.call',{sessionId:'s',operation:'extension:invoke-action',payload:s.calls[ps.length].args})));await copy;assert.deepEqual(effects.at(-1),{text:scenario.copy});checks++;
   const oldCount=effects.length;await rpc('session.call',{sessionId:'s',operation:'extension:invoke-action',payload:{actionId:token}});assert.equal(effects.length,oldCount);checks++;
   // New deliberate copy after success uses newly issued token.
   const again=s.surface.actions.find(a=>a.kind==='copy').id,p=s.surface.onInvokeAction(again);s.calls[ps.length+1].resolve(annotate(await rpc('session.call',{sessionId:'s',operation:'extension:invoke-action',payload:s.calls[ps.length+1].args})));await p;assert.deepEqual(effects.at(-1),{text:scenario.copy});checks++;s.h.stop();await rpc('session.dispose',{sessionId:'s'});
  }
  // Real native application followed by a lost/failed HOST reply: the visible
  // Refresh button recovers the exact current draft, without reissuing input.
  {const opened=await rpc('session.open',{sessionId:'s',commandName:'ip2long',preferences:{},argumentValues:{keywork:'1.2.3.4'},searchText:null});
   const reset=await rpc('session.call',{sessionId:'s',operation:'extension:invoke-action',payload:{actionId:'control:choice',formValues:{value:'IPv4'}}});
   const s=setup(annotate(reset)),cb=s.surface;
   const p=cb.onSearchTextChanged('::1');await rpc('session.call',{sessionId:'s',operation:'extension:invoke-action',payload:s.calls[0].args});s.calls[0].resolve({ok:false,message:'Lost input reply'});await p;
   const control=s.surface.onInvokeAction('control:choice',{value:'IPv6'});await rpc('session.call',{sessionId:'s',operation:'extension:invoke-action',payload:s.calls[1].args});s.calls[1].reject(new Error('Lost control reply'));await control;
   const count=effects.length;await cb.onInvokeAction(reset.actions.find(a=>a.kind==='copy').id);assert.equal(effects.length,count);checks++;
   const button=find(s.tree(),'Button');assert(button);button.props.onClick();assert.equal(s.calls[2].kind,'refresh');
   s.calls[2].resolve(annotate(await rpc('session.call',{sessionId:'s',operation:'extension:refresh-session',payload:{}})));await new Promise(r=>setImmediate(r));
   assert.equal(s.surface.root.props.searchText,'::1');assert.equal(s.surface.root.props.__clientRevision,2);assert(s.surface.actions.some(a=>a.kind==='copy'));checks+=3;s.h.stop();await rpc('session.dispose',{sessionId:'s'});
  }
 }finally{await rpc('shutdown',{});proc.stdin.end();await (proc.exitCode===null?new Promise((resolve,reject)=>proc.once('exit',code=>code===0?resolve():reject(new Error('process '+code)))):Promise.resolve(assert.equal(proc.exitCode,0)))}
 return checks;
};

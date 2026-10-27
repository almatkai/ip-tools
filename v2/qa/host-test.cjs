const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),ts=require(path.join(root,'.work/v1/node_modules/typescript'));
const deferred=()=>{let resolve,reject;const promise=new Promise((r,j)=>{resolve=r;reject=j});return {promise,resolve,reject}};
class Hooks {
 constructor(){this.slots=[];this.i=0;this.effects=[];this.clean=[];this.deps=[];this.react={
  useState:v=>{const i=this.i++;if(!(i in this.slots))this.slots[i]=typeof v==='function'?v():v;return [this.slots[i],n=>this.slots[i]=typeof n==='function'?n(this.slots[i]):n]},
  useRef:v=>{const i=this.i++;return this.slots[i]??(this.slots[i]={current:v})},
  useMemo:(f,d)=>{const i=this.i++;if(!this.deps[i]||d.some((v,j)=>v!==this.deps[i][j])){this.slots[i]=f();this.deps[i]=d}return this.slots[i]},
  useCallback:(f)=>{this.i++;return f},
  useEffect:(f,d)=>{const i=this.i++;if(!this.deps[i]||d.some((v,j)=>v!==this.deps[i][j])){this.effects.push(()=>{this.clean[i]?.();this.clean[i]=f()});this.deps[i]=d}},
 };}
 render(fn,props){this.i=0;const tree=fn(props);for(const f of this.effects.splice(0))f();return tree}
 stop(){for(const f of this.clean)f?.()}
}
const jsx=(type,props)=>({type,props:props??{}});
function load(file,hooks,extras={}){
 const output=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{esModuleInterop:true,target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
 const module={exports:{}};
 const context={module,exports:module.exports,require:n=>{
  if(n==='react')return hooks.react;if(n==='react/jsx-runtime')return {jsx,jsxs:jsx,Fragment:'Fragment'};
  if(n==='./src/raycast-api')return {ExtensionRuntimeSurface:'Surface'};
  if(n==='./hooks')return {setRuntimeContext(){},NavigationContext:{Provider:'NavigationProvider'}};
  if(n==='./extensionSessionRefresh')return {startSessionRefresh:o=>{extras.refresh=o.refresh;return ()=>{}}};
  if(n.endsWith('/primitives')||n==='./ui/primitives')return new Proxy({cx:(...x)=>x.join(' ')},{get:(o,k)=>o[k]??String(k)});
  if(n.endsWith('/colorConverter'))return {buildColorConversionResults:()=>[]};return new Proxy({},{get:(_,k)=>String(k)});
 },window:extras.window??{tezbar:{}},document:{visibilityState:'visible'},console:{log(){},error(){}},setTimeout:()=>1,clearTimeout(){}};
 new vm.Script(output,{filename:file}).runInContext(vm.createContext(context),{timeout:2000});return module.exports;
}
function find(tree,type){if(!tree)return;if(Array.isArray(tree)){for(const t of tree){const r=find(t,type);if(r)return r}}else {if(tree.type===type)return tree;return find(tree.props?.children,type)}}
function model(text){return {ok:true,mode:'view',refreshMs:null,sessionId:'s',generation:'g',extensionId:'x',commandName:'ip2long',title:'IP Tools',root:{type:'List',props:{searchText:text,__hasServerSearch:true}},actions:[]}}
async function test(mode){
 const dir=path.join(root,mode==='patched'?'.work/host-patched':'qa/fixtures/host');let checks=0;
 const h=new Hooks(),pending=[],extras={window:{setTimeout:()=>1,clearTimeout(){},tezbar:{extensionDisposeSession:async()=>{},extensionSearchTextChanged:()=>{const d=deferred();pending.push(d);return d.promise},extensionInvokeAction:()=>{const d=deferred();pending.push(d);return d.promise},extensionRefreshSession:()=>{const d=deferred();pending.push(d);return d.promise}}}};
 const View=load(path.join(dir,'src/renderer/ExtensionRuntimeView.tsx'),h,extras).default;
 const props={initial:model('A'),onBack(){}};let tree=h.render(View,props),surface=find(tree,'Surface');
 const refresh=extras.refresh();const action=surface.props.onInvokeAction('copy:old');
 const a=surface.props.onSearchTextChanged('A'),b=surface.props.onSearchTextChanged('B'),a2=surface.props.onSearchTextChanged('A');
 if(mode==='patched'){assert.equal(pending.length,5);await extras.refresh();assert.equal(pending.length,5);checks++;await surface.props.onInvokeAction('copy:blocked');assert.equal(pending.length,5);checks++;}
 pending[3].resolve(model('B'));await b;pending[2].resolve(model('A-old'));await a;pending[4].resolve(model('A-current'));await a2;
 tree=h.render(View,props);assert.equal(find(tree,'Surface').props.root.props.searchText,'A-current');checks++;
 pending[0].resolve(model('refresh-stale'));await refresh;pending[1].resolve(model('action-stale'));await action;
 tree=h.render(View,props);assert.equal(find(tree,'Surface').props.root.props.searchText,'A-current');checks++;
 h.stop();
 const l=new Hooks(),sent=[],lp={root:model('A').root,title:'IP Tools',commandName:'ip2long',actions:[],onBack(){},onRunPrimaryAction(){},onOpenActions(){},onSearchTextChanged:x=>sent.push(x),onLoadMore(){}};
 const List=load(path.join(dir,'src/renderer/src/raycast-api/list-runtime.tsx'),l).ListRuntime;
 tree=l.render(List,lp);find(tree,'input').props.onChange({target:{value:'B'}});assert.deepEqual(sent,['B']);checks++;
 lp.root=model('A').root;tree=l.render(List,lp);tree=l.render(List,lp);assert.equal(find(tree,'input').props.value,'B');checks++;
 find(tree,'input').props.onChange({target:{value:'A'}});find(tree,'input').props.onChange({target:{value:'invalid'}});assert.deepEqual(sent,['B','A','invalid']);checks++;
 lp.root={type:'List',props:{searchText:'invalid',__hasServerSearch:true},children:[{type:'List.EmptyView',props:{title:'Please enter a valid IP address！',icon:{source:'XMarkCircle',tintColor:'red'}}}]};tree=l.render(List,lp);function text(x){if(x==null)return '';if(Array.isArray(x))return x.map(text).join('');if(typeof x==='string')return x;return text(x.props?.children)}assert(text(tree).includes('Please enter a valid IP address！'));checks++;
 l.stop();return checks;
}
async function listChecks(){let checks=0; const l=new Hooks(),sent=[],lp={root:model('A').root,title:'IP Tools',commandName:'ip2long',actions:[],onBack(){},onRunPrimaryAction(){},onOpenActions(){},onSearchTextChanged:x=>sent.push(x),onLoadMore(){}};
 const List=load(path.join(root,'.work/host-patched','src/renderer/src/raycast-api/list-runtime.tsx'),l).ListRuntime;
 tree=l.render(List,lp);find(tree,'input').props.onChange({target:{value:'B'}});assert.deepEqual(sent,['B']);checks++;
 lp.root=model('A').root;tree=l.render(List,lp);tree=l.render(List,lp);assert.equal(find(tree,'input').props.value,'B');checks++;
 find(tree,'input').props.onChange({target:{value:'A'}});find(tree,'input').props.onChange({target:{value:'invalid'}});assert.deepEqual(sent,['B','A','invalid']);checks++;
 lp.root={type:'List',props:{searchText:'invalid',__hasServerSearch:true},children:[{type:'List.EmptyView',props:{title:'Please enter a valid IP address！',icon:{source:'XMarkCircle',tintColor:'red'}}}]};tree=l.render(List,lp);function text(x){if(x==null)return '';if(Array.isArray(x))return x.map(text).join('');if(typeof x==='string')return x;return text(x.props?.children)}assert(text(tree).includes('Please enter a valid IP address！'));checks++;
 l.stop();return checks;
}
function retryReachability(){
 const value=JSON.parse(fs.readFileSync(path.join(root,'.work/multi-retry-view.json'),'utf8'));
 const retry=value.actions.find(a=>a.title==='Retry Exact Copy');assert(retry);
 const h=new Hooks(),Surface=load(path.join(root,'qa/fixtures/host/src/renderer/src/raycast-api/index.tsx'),h,{window:{tezbar:{},addEventListener(){},removeEventListener(){}}}).ExtensionRuntimeSurface;
 const props={sessionId:'s',title:'IP Tools',extensionId:'x',commandName:'ip2long',root:value.root,actions:value.actions,onBack(){},onSearchTextChanged(){},onLoadMore(){},onInvokeAction(){}};
 let tree=h.render(Surface,props);const list=find(tree,'ListRuntime');assert(list);
 list.props.onOpenActions(value.root.children.find(n=>n.type==='List.Item').props.actionIds);
 tree=h.render(Surface,props);assert(find(tree,'ActionPanelOverlay').props.actions.some(a=>a.id===retry.id),'Exact-copy recovery must survive the actual selected-row action filter');h.stop();
 return 1;
}
const watchdog=setTimeout(()=>{console.error('Renderer QA did not complete');process.exitCode=1},30000);
(async()=>{let originalFailed=false;try{await test('original')}catch(e){originalFailed=true}assert(originalFailed,'Original must reproduce ownership failure');const checks=await require('./host-input-tests.cjs')({fs,path,assert,root,Hooks,load,find,model,deferred})+retryReachability()+await listChecks();console.log('full pinned renderer functions:',checks,'checks passed; original failure reproduced');fs.writeFileSync(path.join(root,'.work/renderer-result.json'),JSON.stringify({checks,originalFailed}));})().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>clearTimeout(watchdog));
const titleSource=ts.transpileModule(fs.readFileSync(path.join(root,'qa/fixtures/host/exports/normalizeActionTitle.ts'),'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2022}}).outputText;
const titleContext=vm.createContext({});new vm.Script(titleSource).runInContext(titleContext);assert.equal(vm.runInContext("normalizeActionTitle('Action.CopyToClipboard', {})",titleContext),'Copy to Clipboard');

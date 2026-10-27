// Read-only actual TSX evaluation. No Node builtins, real Raycast runtime,
// network, clipboard or filesystem are made available to evaluated modules.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const base=path.resolve(__dirname,'../.work/v1');
const ts=require(path.join(base,'node_modules/typescript'));
const toolkit=require(path.join(base,'node_modules/ip-toolkit'));
const JSONbig=require(path.join(base,'node_modules/json-bigint'));
const nativeJSON=JSON;
const list=['List','Item','EmptyView','Dropdown','Section'];
const List=Object.fromEntries(list.slice(1).map(k=>[k,'List.'+k]));
List.Dropdown={Item:'List.Dropdown.Item',Section:'List.Dropdown.Section'};
const Action={CopyToClipboard:'CopyToClipboard'};
function evaluate(command,input,choice='IPv4',geo={status:'success',query:'127.0.0.1'}) {
 let slot=0,states=[],promises=[],requests=[];const draft=input?input:'';
 if(command==='geoLocation')states=[draft,choice==='IPv4'?'en':choice];
 else if(command==='toIPv6Format')states=[draft];
 else states=[choice,draft];
 const jsx=(type,props)=>({type:type===List?'List':type===List.Dropdown?'List.Dropdown':type,props:props??{}});
 const mocks={
  react:{useState:()=>[states[slot++],()=>{}]},
  'react/jsx-runtime':{jsx,jsxs:jsx,Fragment:'Fragment'},
  'ip-toolkit':toolkit,'json-bigint':JSONbig,
  axios:async url=>{requests.push(url);return {data:geo}},
  '@raycast/utils':{usePromise:(producer,args)=>{promises.push(producer(...args));return {isLoading:false,data:geo}}},
  '@raycast/api':{List,Action,ActionPanel:'ActionPanel',Icon:new Proxy({},{get:(_,k)=>k}),Color:{Green:'green',Red:'red',Yellow:'yellow'}},
 };
 function load(file) {
  const output=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{esModuleInterop:true,target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
  const module={exports:{}};
  const context=vm.createContext({module,exports:module.exports,require:name=>{
    if(name==='./components/dropdown')return load(path.join(base,'src/components/dropdown.tsx'));
    if(!(name in mocks))throw Error('Unmocked source import '+name);return mocks[name];
  }});
  new vm.Script(output,{filename:path.basename(file)}).runInContext(context,{timeout:1000});return module.exports;
 }
 try {
  const tree=load(path.join(base,'src',command+'.tsx')).default({arguments:{keywork:input}});
  const rows=[],empty=[];
  function walk(x){if(!x)return;if(Array.isArray(x)){x.forEach(walk);return;}if(x.type==='List.Item') {
    const copies=[];function actions(a){if(!a)return;if(Array.isArray(a)){a.forEach(actions);return}if(a.type==='CopyToClipboard')copies.push({title:a.props.title??'Copy to Clipboard',text:String(a.props.content)});actions(a.props?.children)}actions(x.props.actions);
    rows.push({title:x.props.title,subtitle:x.props.subtitle,copies});
   } else if(x.type==='List.EmptyView')empty.push({title:x.props.title,icon:x.props.icon});walk(x.props?.children)}walk(tree);
  return Promise.all(promises).then(()=>({rows,empty,requests,placeholder:tree.props.searchBarPlaceholder}));
 }catch(e){return Promise.resolve({error:e.name});}
}
module.exports={evaluate};
if(require.main===module){let text='';process.stdin.setEncoding('utf8');process.stdin.on('data',s=>text+=s);process.stdin.on('end',async()=>{for(const q of nativeJSON.parse(text))process.stdout.write(nativeJSON.stringify(await evaluate(q.command,q.input,q.choice,q.geo))+'\n')});}

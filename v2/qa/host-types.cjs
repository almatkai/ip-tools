// Isolated compiler diagnostics against exact Git-object bridge/shared definitions.
// No host checkout build or dependency installation. UI boundary is explicitly stubbed.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),ts=require(path.join(root,'.work/v1/node_modules/typescript'));
const pin='ea100cee3f69711de12485ba061950c5fc65258f',host=path.resolve(root,'../../../Tezbar'),work=path.join(root,'.work/host-contract-types');
const files=new Map(),objects={};
function fetch(name){if(files.has(name))return;const body=cp.execFileSync('git',['-C',host,'show',pin+':'+name],{encoding:'utf8'});files.set(name,body);objects[name]=crypto.createHash('sha256').update(body).digest('hex');for(const m of body.matchAll(/(?:from\s+|import\s*\()['"](\.[^'"]+)['"]/g)){const p=path.posix.normalize(path.posix.join(path.posix.dirname(name),m[1]));if(p.startsWith('src/shared/'))fetch(p.endsWith('.ts')?p:p+'.ts')}}
fetch('src/shared/desktop-api.ts');fetch('src/shared/extensionRuntime.ts');
const surface=fs.readFileSync(path.join(root,'qa/fixtures/host/src/renderer/src/raycast-api/index.tsx'),'utf8');
const ast=ts.createSourceFile('surface.tsx',surface,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX),props=ast.statements.find(s=>ts.isTypeAliasDeclaration(s)&&s.name.text==='ExtensionRuntimeSurfaceProps').getText(ast);
const boundary=`import type { ExtensionRuntimeAction, ExtensionRuntimeNode } from '../../../shared/extensionRuntime';\n${props}\nexport declare function ExtensionRuntimeSurface(props: ExtensionRuntimeSurfaceProps): import('react').ReactNode;`;
function write(file,body){const p=path.join(work,file);fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,body)}
for(const [name,body] of files)write(name,body);
write('src/renderer/src/raycast-api/index.tsx',boundary);
write('src/renderer/ui/primitives.tsx',"import type { ComponentType } from 'react';export declare const Button:ComponentType<any>,Message:ComponentType<any>;");
write('src/renderer/extensionSessionRefresh.ts',fs.readFileSync(path.join(root,'qa/fixtures/host/src/renderer/extensionSessionRefresh.ts'),'utf8'));
write('contracts.ts',`import type {RaymesApi} from './src/shared/desktop-api';\nimport type {ExtensionInvokeActionRequest} from './src/shared/extensionRuntime';
declare global {interface Window {tezbar: RaymesApi}}
const request:ExtensionInvokeActionRequest={sessionId:'s',actionId:'control:input',formValues:{searchText:'::1',value:'IPv6',revision:3}};
const bridge:Parameters<RaymesApi['extensionInvokeAction']>[0]=request;
// @ts-expect-error Client draft uses existing formValues; no new top-level wire field exists.
const invalid:ExtensionInvokeActionRequest={sessionId:'s',actionId:'control:input',revision:3};\n`);
const options={strict:true,noEmit:true,target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,moduleResolution:ts.ModuleResolutionKind.Node10,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true,skipLibCheck:true,types:[],baseUrl:work,paths:{react:[path.join(root,'.work/v1/node_modules/@types/react')],'react/*':[path.join(root,'.work/v1/node_modules/@types/react/*')]}};
function diagnostics(mode){write('src/renderer/ExtensionRuntimeView.tsx',fs.readFileSync(path.join(root,mode==='baseline'?'qa/fixtures/host/src/renderer/ExtensionRuntimeView.tsx':'.work/host-patched/src/renderer/ExtensionRuntimeView.tsx'),'utf8'));write('src/shared/extensionRuntime.ts',fs.readFileSync(path.join(root,mode==='baseline'?'qa/fixtures/host/src/shared/extensionRuntime.ts':'.work/host-patched/src/shared/extensionRuntime.ts'),'utf8'));
 const p=ts.createProgram([path.join(work,'contracts.ts'),path.join(work,'src/renderer/ExtensionRuntimeView.tsx')],options);
 return ts.getPreEmitDiagnostics(p).map(d=>({file:d.file?path.relative(work,d.file.fileName):'',code:d.code,message:ts.flattenDiagnosticMessageText(d.messageText,' ')}));}
const baseline=diagnostics('baseline'),proposed=diagnostics('proposed'),key=d=>JSON.stringify(d),counts=new Map();for(const d of baseline)counts.set(key(d),(counts.get(key(d))||0)+1);const added=[];for(const d of proposed){const k=key(d),n=counts.get(k)||0;if(n)counts.set(k,n-1);else added.push(d)}
fs.writeFileSync(path.join(root,'.work/host-types-result.json'),JSON.stringify({pin,objects,compiler:ts.version,boundaries:'Full component, full actual shared/desktop bridge definitions and exact extracted Surface props; React types from locked V1 QA, primitives declarations only. No full host build.',baseline,proposed,added},null,2)+'\n');assert.deepEqual(added,[]);console.log('Pinned bridge/shared/compiler contracts: no new diagnostics;',baseline.length,'baseline,',proposed.length,'proposed diagnostics retained/documented');

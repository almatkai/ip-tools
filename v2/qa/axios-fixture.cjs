const http=require('node:http'),https=require('node:https'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),axios=require(path.join(root,'.work/v1/node_modules/axios/dist/node/axios.cjs'));
const {evaluate}=require('./oracle.cjs');
const body='{"status":"success","query":"::1","country":"Fixture","large":9007199254740993,"tiny":0.0000001,"whole":1.0}';
async function listen(s){await new Promise(r=>s.listen(0,'127.0.0.1',r));return s.address().port}
async function close(s){await new Promise(r=>s.close(r))}
(async()=>{let requests=[];const handle=(req,res)=>{requests.push(req.url);res.setHeader('Content-Type','application/json');res.end(body)};
 const plain=http.createServer(handle),tls=https.createServer({key:fs.readFileSync(path.join(root,'.work/certs/leaf-key.pem')),cert:fs.readFileSync(path.join(root,'.work/certs/leaf.pem'))},handle);
 try {const hp=await listen(plain),sp=await listen(tls);const url='/json/::1?lang=zh-CN&&fields=61151';const a=(await axios(`http://127.0.0.1:${hp}${url}`,{proxy:false})).data;
 const b=(await axios(`https://127.0.0.1:${sp}${url}`,{proxy:false,httpsAgent:new https.Agent({ca:fs.readFileSync(path.join(root,'.work/certs/cert.pem'))})})).data;
 assert.deepEqual(a,b);assert.equal(a.large,9007199254740992);assert.deepEqual(requests,[url,url]);
 for(const input of ['', ' ', '::1','invalid'])for(const lang of ['en','zh-CN']){
  const source=await evaluate('geoLocation',input,lang,a);
  assert.deepEqual(source.requests,input==='invalid'?[]:[`http://ip-api.com/json/${input}?lang=${lang}&&fields=61151`]);
  assert.equal(source.empty.length,input==='invalid'?1:0);
 }
 console.log('Locked axios 1.20.0 own HTTP/TLS fixtures + 8 actual geo source producer cases passed');
 fs.writeFileSync(path.join(root,'.work/axios-result.json'),JSON.stringify({http:true,tls:true,sourceGeoCases:8,numberRounding:true}));
 }finally{await close(plain);await close(tls)}})().catch(e=>{console.error(e);process.exitCode=1});

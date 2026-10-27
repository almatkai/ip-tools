"""Own loopback TLS CA. Trust override exists only in ignored QA helper."""
import pathlib,subprocess,ssl,threading,http.server,json,os
ROOT=pathlib.Path(__file__).resolve().parents[1];WORK=ROOT/'.work';certs=WORK/'certs';certs.mkdir(exist_ok=True)
conf='''[req]
distinguished_name=dn
x509_extensions=ext
prompt=no
[dn]
CN=IP Tools QA fixture
[ext]
subjectAltName=IP:127.0.0.1
basicConstraints=critical,CA:TRUE
keyUsage=critical,keyCertSign,digitalSignature,keyEncipherment
'''
(certs/'openssl.cnf').write_text(conf)
subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','2','-config',str(certs/'openssl.cnf'),'-keyout',str(certs/'key.pem'),'-out',str(certs/'cert.pem')],check=True,capture_output=True)
(certs/'leaf.cnf').write_text(conf.replace('CA:TRUE','CA:FALSE').replace('keyCertSign,','').replace('CN=IP Tools QA fixture','CN=127.0.0.1'))
subprocess.run(['openssl','req','-new','-newkey','rsa:2048','-nodes','-config',str(certs/'leaf.cnf'),'-keyout',str(certs/'leaf-key.pem'),'-out',str(certs/'leaf.csr')],check=True,capture_output=True)
subprocess.run(['openssl','x509','-req','-in',str(certs/'leaf.csr'),'-CA',str(certs/'cert.pem'),'-CAkey',str(certs/'key.pem'),'-CAcreateserial','-days','2','-extfile',str(certs/'leaf.cnf'),'-extensions','ext','-out',str(certs/'leaf.pem')],check=True,capture_output=True)
helper=WORK/'tls-helper';(helper/'src').mkdir(parents=True,exist_ok=True)
(helper/'Cargo.toml').write_text('''[package]
name="ip-tools-unshipped-tls-qa"
version="0.0.0"
edition="2021"
rust-version="1.85"
[workspace]
[dependencies]
tezbar-ip-tools={path="../.."}
reqwest={version="=0.12.28",default-features=false,features=["rustls-tls"]}
tokio={version="1",features=["macros","rt-multi-thread"]}
''')
(helper/'src/main.rs').write_text('''#[tokio::main(worker_threads=2)] async fn main(){
let args:Vec<String>=std::env::args().collect();
let production=tezbar_ip_tools::net::client().unwrap();
assert!(tezbar_ip_tools::net::fetch(&production,&args[2]).await.is_err(),"Production must reject fixture CA");
let cert=reqwest::Certificate::from_pem(&std::fs::read(&args[1]).unwrap()).unwrap();
let qa=reqwest::Client::builder().add_root_certificate(cert).build().unwrap();
let result=tezbar_ip_tools::net::fetch(&qa,&args[2]).await.unwrap();println!("{}",result);
}''')
# Reuse the exact application lock resolution; helper's own package is lock-updated locally.
(helper/'Cargo.lock').write_bytes((ROOT/'qa/locks/tls-helper.Cargo.lock').read_bytes())
subprocess.run([str(ROOT/'qa/env.sh'),'cargo','build','--locked','--manifest-path',str(helper/'Cargo.toml'),'--config','resolver.incompatible-rust-versions="fallback"'],check=True,stdout=open(WORK/'tls-build.log','w'),stderr=subprocess.STDOUT)
class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  assert self.path=='/json/::1?lang=en&&fields=61151',self.path
  body=b'{"status":"success","query":"::1","country":"TLS fixture","large":9007199254740993,"tiny":0.0000001,"whole":1.0}'
  self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(str(certs/'leaf.pem'),str(certs/'leaf-key.pem'));server.socket=context.wrap_socket(server.socket,server_side=True)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
 p=subprocess.run([str(WORK/'target/debug/ip-tools-unshipped-tls-qa'),str(certs/'cert.pem'),f'https://127.0.0.1:{server.server_port}/json/::1?lang=en&&fields=61151'],capture_output=True,text=True)
 assert p.returncode==0,p.stderr
 result=json.loads(p.stdout);assert result['country']=='TLS fixture' and result['large']==9007199254740992;assert '1e-7'in p.stdout;assert '"whole":1}'in p.stdout
 print('TLS: production private-CA rejection + separate unshipped trusted helper success')
 (WORK/'tls-result.json').write_text(json.dumps(dict(productionPrivateCaRejected=True,qaTrustedTlsSuccess=True,response=result)))
finally:server.shutdown();server.server_close();thread.join()

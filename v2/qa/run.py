"""Reproducible isolated QA. --full additionally builds a fresh DEV archive."""
from pathlib import Path
import subprocess,os,sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parent;WORK=ROOT/'.work';WORK.mkdir(exist_ok=True);LOGS=WORK/'run-logs';LOGS.mkdir(exist_ok=True);results=[]
assert Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=REPO,text=True).strip())==REPO
assert Path(os.environ.get('CARGO_HOME','')).is_relative_to(WORK),'Run through qa/env.sh'
PYTHON=sys.executable

def step(name,args,allow_tooling_block=False):
 with (LOGS/(name+'.log')).open('w') as log:p=subprocess.run(args,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
 result={'name':name,'exit':p.returncode,'log':str((LOGS/(name+'.log')).relative_to(ROOT))}
 if p.returncode and allow_tooling_block:
  text=(LOGS/(name+'.log')).read_text();assert any(s in text for s in ['x86_64-w64-mingw32-gcc','dlltool','target may not be installed']),text[-4000:];result['state']='tooling-blocked'
 else:
  assert p.returncode==0,(name,p.returncode,result['log']);result['state']='passed'
 results.append(result);print(name+': '+result['state'],flush=True)

def py(name,file,*args):step(name,[PYTHON,str(ROOT/'qa'/file),*args])
def cargo(name,*args):step(name,['cargo',*args,'--manifest-path',str(ROOT/'Cargo.toml')])
BASE='95d41603aa6fccefe31f507c70f21e35e24c69f4';v1=WORK/'v1';v1.mkdir(exist_ok=True)
for name in subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=REPO,text=True).splitlines():
 p=v1/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(subprocess.check_output(['git','show',BASE+':'+name],cwd=REPO))
lock_before=hashlib.sha256((v1/'package-lock.json').read_bytes()).hexdigest()
step('v1-npm-ci',['npm','ci','--ignore-scripts','--prefix',str(v1)])
assert lock_before==hashlib.sha256((v1/'package-lock.json').read_bytes()).hexdigest()
step('v1-tests',['npm','test','--prefix',str(v1)])
step('v1-typecheck',['npm','run','typecheck','--prefix',str(v1)])
step('schema-npm-ci',['npm','ci','--ignore-scripts','--prefix',str(ROOT/'qa/schema')])
py('references','references.py')
cargo('fmt','fmt','--check')
cargo('tests','test','--locked')
step('strict-clippy',['cargo','clippy','--locked','--all-targets','--manifest-path',str(ROOT/'Cargo.toml'),'--','-D','warnings'])
step('msrv-tests',['cargo','+1.85.0','test','--locked','--manifest-path',str(ROOT/'Cargo.toml')])
step('msrv-clippy',['cargo','+1.85.0','clippy','--locked','--all-targets','--manifest-path',str(ROOT/'Cargo.toml'),'--','-D','warnings'])
cargo('build','build','--locked')
py('source-oracle','parity.py')
py('sdk-pipe-oracle','protocol.py')
py('lifecycle','lifecycle.py')
py('host-patch','host_patch.py')
step('full-renderer',['node',str(ROOT/'qa/host-test.cjs')])
step('pinned-host-types',['node',str(ROOT/'qa/host-types.cjs')])
py('full-host-producer','host-producer.py')
py('whole-geo-http','geo_session.py')
py('separate-tls-helper','tls.py')
step('locked-axios-fixtures',['node',str(ROOT/'qa/axios-fixture.cjs')])
step('full-schema',['node',str(ROOT/'qa/schema-test.cjs')])
cargo('fetch-all-targets','fetch','--locked')
py('cargo-archives','audit.py')
py('npm-archives','audit.py','npm')
for kind in ['check','clippy']:
 args=['cargo',kind,'--locked','--target','x86_64-pc-windows-gnu','--manifest-path',str(ROOT/'Cargo.toml')]
 if kind=='clippy':args+=['--all-targets','--','-D','warnings']
 step('windows-'+kind,args,True)
if '--full'in sys.argv:
 py('fresh-arm64','fresh-build.py')
 py('dev-package','package.py')
step('diff-whitespace',['git','diff','--check'])
(WORK/'run-result.json').write_text(json.dumps(results,indent=2)+'\n')
print('QA finished. No stage/commit/push/install/release. Candidate inventory is generated after documentation finalization.')

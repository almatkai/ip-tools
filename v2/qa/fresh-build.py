import pathlib,tempfile,subprocess,os,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1];WORK=ROOT/'.work';REV='e955911f0bf5b558f9d3eb5183df0adc95c22af2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():return {str(p.relative_to(ROOT)):sha(p) for p in sorted(list((ROOT/'src').glob('*'))+[ROOT/'Cargo.toml',ROOT/'Cargo.lock',ROOT/'extension.json']) if p.is_file()}
before=inputs();fresh=pathlib.Path(tempfile.mkdtemp(prefix='fresh-',dir=WORK));home=fresh/'cargo-home';target=fresh/'target';home.mkdir();target.mkdir();assert not list(home.iterdir()) and not list(target.iterdir())
cmd=[str(ROOT/'qa/env.sh'),'env','CARGO_HOME='+str(home),'CARGO_TARGET_DIR='+str(target),'cargo','+stable','build','--release','--locked','--target','aarch64-apple-darwin','--manifest-path',str(ROOT/'Cargo.toml')]
with (fresh/'build.log').open('w') as log:subprocess.run(cmd,check=True,stdout=log,stderr=subprocess.STDOUT)
assert inputs()==before,'Source/lock changed during isolated build'
checkouts=list((home/'git/checkouts').glob('tezbar-extension-sdk-rust-*/*'));matches=[]
for checkout in checkouts:
 if not checkout.is_dir():continue
 head=subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()
 if head==REV:matches.append(checkout)
assert len(matches)==1,matches
sdk={}
for fixture in (ROOT/'qa/fixtures/sdk').rglob('*'):
 if fixture.is_file():
  relative=fixture.relative_to(ROOT/'qa/fixtures/sdk');fetched=matches[0]/relative;assert fixture.read_bytes()==fetched.read_bytes(),relative;sdk[str(relative)]=sha(fetched)
binary=target/'aarch64-apple-darwin/release/tezbar-ip-tools'
kind=subprocess.check_output(['file',str(binary)],text=True).strip().split(': ',1)[1];assert 'arm64'in kind,kind
info=json.loads(subprocess.check_output([str(binary),'--protocol-info'],text=True));assert info['sdkVersion']=='0.1.1' and len(info['commands'])==9
report=dict(binary=str(binary.relative_to(ROOT)),binarySha256=sha(binary),architecture=kind,freshCargoHome=str(home.relative_to(ROOT)),freshTarget=str(target.relative_to(ROOT)),sourceBefore=before,sourceAfter=inputs(),sdkRevision=REV,sdkFixtures=sdk,protocolInfo=info)
(WORK/'fresh-build-result.json').write_text(json.dumps(report,indent=2)+'\n');print('Fresh immutable-HTTPS ARM64 production build:',report['binarySha256'])

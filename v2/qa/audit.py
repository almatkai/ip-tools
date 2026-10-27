"""Authentic archive checksums and grants; never fabricate license text."""
import pathlib,hashlib,json,tarfile,tomllib,re,urllib.request,base64,concurrent.futures,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];WORK=ROOT/'.work'
def digest(b):return hashlib.sha256(b).hexdigest()
def grant(name):
 b=pathlib.PurePosixPath(name).name.lower()
 return any(t in b for t in ('license','licence','copying','copyright','notice','authors')) and not b.endswith(('.rs','.go','.c','.h','.py','.js','.json'))
def extract(archive,dest):
 records=[]
 with tarfile.open(archive,'r:*') as tar:
  for m in tar:
   if m.isfile() and grant(m.name):
    parts=pathlib.PurePosixPath(m.name).parts[1:]
    if not parts or '..' in parts:raise ValueError('unsafe archive')
    b=tar.extractfile(m).read();p=dest.joinpath(*parts);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);records.append(dict(path=str(p.relative_to(ROOT)),sha256=digest(b)))
 return records

def cargo(home,lockfile=None,label='cargo'):
 lock=tomllib.loads((lockfile or ROOT/'Cargo.lock').read_text());result=[]
 for p in lock['package']:
  if 'checksum'not in p:continue
  matches=list((home/'registry/cache').glob(f"*/{p['name']}-{p['version']}.crate"));assert len(matches)==1,(p,matches)
  archive=matches[0];sha=digest(archive.read_bytes());assert sha==p['checksum']
  records=extract(archive,(ROOT/'notices/cargo' if label=='cargo' else ROOT/'qa/notices'/label)/f"{p['name']}-{p['version']}")
  result.append(dict(name=p['name'],version=p['version'],archiveSha256=sha,grants=records,missingLicenseText=not any(('license' in x['path'].lower() or 'licence' in x['path'].lower()) or 'copying' in x['path'].lower() or b'Permission is hereby granted' in (ROOT/x['path']).read_bytes() for x in records)))
 (ROOT/('qa/'+label+'-archive-audit.json')).write_text(json.dumps(result,indent=2)+'\n');print('Cargo archives:',len(result),'missing grants:',[(p['name'],p['version']) for p in result if p['missingLicenseText']])

def npm(lockfile=None,label='npm'):
 lock=json.loads((lockfile or ROOT.parent/'package-lock.json').read_text());cache=WORK/'npm-archives';cache.mkdir(exist_ok=True)
 def one(kp):
  k,p=kp;url=p['resolved'];name=k.replace('node_modules/','').replace('/node_modules/','--');archive=cache/(name.replace('/','__')+'-'+p['version']+'.tgz');archive.parent.mkdir(parents=True,exist_ok=True)
  if not archive.exists():
   for attempt in range(4):
    try:
     with urllib.request.urlopen(url,timeout=30) as r:archive.write_bytes(r.read())
     break
    except Exception:
     if attempt==3:raise
  b=archive.read_bytes();algorithm,want=p['integrity'].split('-',1);actual=base64.b64encode(hashlib.new(algorithm,b).digest()).decode();assert actual==want,(k,'SRI mismatch')
  records=extract(archive,ROOT/'qa/notices'/label/name)
  members=[];embedded=[]
  with tarfile.open(archive,'r:*') as tar:
   for member in tar:
    if member.isfile():
     members.append(member.name)
     content=tar.extractfile(member).read()
     if (b'Permission is hereby granted' in content and b'THE SOFTWARE IS PROVIDED' in content) or (b'Apache License' in content and b'TERMS AND CONDITIONS FOR USE' in content):
      embedded.append(member.name)
      if not records and pathlib.PurePosixPath(member.name).name.lower().startswith('readme'):
       dest=ROOT/'qa/notices'/label/name/'README.grant.md';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content);records.append(dict(path=str(dest.relative_to(ROOT)),sha256=digest(content),archiveMember=member.name))
  return dict(packagePath=k,version=p['version'],url=url,sri=p['integrity'],sha256=digest(b),archiveMembers=members,embeddedGrantCandidates=embedded,grants=records,missingLicenseText=not embedded and not any(('license'in x['path'].lower() or 'licence'in x['path'].lower()) or 'copying'in x['path'].lower() for x in records))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:result=list(pool.map(one,[(k,p) for k,p in lock['packages'].items() if k]))
 (ROOT/('qa/'+label+'-archive-audit.json')).write_text(json.dumps(result,indent=2)+'\n');print('npm archives:',len(result),'missing grants:',[(p['packagePath'],p['version']) for p in result if p['missingLicenseText']])
if __name__=='__main__':
 import sys
 if len(sys.argv)>1 and sys.argv[1]=='npm':
  npm();npm(ROOT/'qa/schema/package-lock.json','schema-npm')
 else:
  home=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else WORK/'cargo-home'
  cargo(home)
  for label in ['host-producer','tls-helper']:
   subprocess.run([str(ROOT/'qa/env.sh'),'cargo','fetch','--locked','--manifest-path',str(WORK/label/'Cargo.toml')],check=True,capture_output=True)
   cargo(home,ROOT/'qa/locks'/(label+'.Cargo.lock'),'cargo-'+label)

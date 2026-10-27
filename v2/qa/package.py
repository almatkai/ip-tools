"""Deterministic development ZIP from a genuine isolated production executable."""
import pathlib,json,hashlib,zipfile,stat,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];WORK=ROOT/'.work'
def sha(b):return hashlib.sha256(b).hexdigest()
def package():
 fresh=json.loads((WORK/'fresh-build-result.json').read_text());binary=ROOT/fresh['binary'];assert sha(binary.read_bytes())==fresh['binarySha256']
 files={'bin/tezbar-ip-tools':(binary.read_bytes(),0o755),'assets/extension_icon.png':((ROOT/'assets/extension_icon.png').read_bytes(),0o644),'LICENSE':((ROOT/'LICENSE').read_bytes(),0o644),'NOTICE':((ROOT/'NOTICE').read_bytes(),0o644)}
 for p in sorted((ROOT/'notices').rglob('*')):
  if p.is_file():files[str(p.relative_to(ROOT))]=(p.read_bytes(),0o644)
 manifest=json.loads((ROOT/'extension.json').read_text());assert manifest['artifacts']=={} and all(v['state']=='not-run'for v in manifest['verification']);manifest['files']={p:sha(b) for p,(b,mode) in sorted(files.items())};files['extension.json']=((json.dumps(manifest,indent=2)+'\n').encode(),0o644)
 archive=WORK/'ip-tools-2.0.0-dev.1-aarch64-apple-darwin-DEV.zip'
 def write(dest):
  with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_STORED) as z:
   for path,(body,mode) in sorted(files.items()):
    info=zipfile.ZipInfo(path,(2026,1,1,0,0,0));info.create_system=3;info.external_attr=(stat.S_IFREG|mode)<<16;z.writestr(info,body)
 write(archive);again=WORK/'repeat-DEV.zip';write(again);assert archive.read_bytes()==again.read_bytes()
 extract=WORK/'package-extracted';extract.mkdir(exist_ok=True)
 # Never use extractall; validate and close the complete expected inventory first.
 inventory=[]
 with zipfile.ZipFile(archive) as z:
  assert set(z.namelist())==set(files) and len(z.namelist())==len(files)
  for info in z.infolist():
   path=pathlib.PurePosixPath(info.filename);assert not path.is_absolute() and '..' not in path.parts
   body=z.read(info);mode=info.external_attr>>16;assert stat.S_ISREG(mode);assert body==files[str(path)][0];assert stat.S_IMODE(mode)==files[str(path)][1]
   target=extract.joinpath(*path.parts);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body);target.chmod(stat.S_IMODE(mode));inventory.append(dict(path=str(path),mode=oct(stat.S_IMODE(mode)),sha256=sha(body)))
 assert {str(p.relative_to(extract)) for p in extract.rglob('*') if p.is_file()}==set(files)
 for path,want in manifest['files'].items():assert sha((extract/path).read_bytes())==want
 subprocess.run([str(ROOT/'qa/env.sh'),'node',str(ROOT/'qa/schema-test.cjs'),str(extract/'extension.json')],check=True)
 info=json.loads(subprocess.check_output([str(extract/'bin/tezbar-ip-tools'),'--protocol-info'],text=True));assert len(info['commands'])==9
 from lifecycle import run
 run(extract/'bin/tezbar-ip-tools')
 # Execute the actual proposed renderer against this freshly extracted process too.
 import os
 subprocess.run(['node',str(ROOT/'qa/host-test.cjs')],env={**os.environ,'IP_TOOLS_QA_BINARY':str(extract/'bin/tezbar-ip-tools')},check=True)
 # Full independent source oracle also runs against extracted production binary.
 from protocol import parity
 parity(extract/'bin/tezbar-ip-tools')
 result=dict(archive=str(archive.relative_to(ROOT)),sha256=sha(archive.read_bytes()),size=archive.stat().st_size,binarySha256=fresh['binarySha256'],inventory=inventory,deterministicArchiveRebuild=True,extractedProductionProtocol=True)
 (WORK/'package-result.json').write_text(json.dumps(result,indent=2)+'\n');print('DEV ZIP:',result['sha256'],len(inventory),'closed regular files')
if __name__=='__main__':package()

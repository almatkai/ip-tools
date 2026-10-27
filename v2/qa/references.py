"""Verify retained exact fixtures and all V1 tracked bytes without sibling working files."""
from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def verify():
 ref=json.loads((ROOT/'qa/reference-hashes.json').read_text());checked=0
 for path,record in ref['v1']['files'].items():
  current=(ROOT.parent/path).read_bytes()
  if path=='README.md':
   assert current.endswith(b'\nStandalone external Rust V2: [implementation and validation](v2/README.md).\n');current=current[:-len(b'\nStandalone external Rust V2: [implementation and validation](v2/README.md).\n')]
  assert sha(current)==record['sha256'],path;checked+=1
 for kind in ['host','sdk']:
  for path,record in ref[kind]['fixtures'].items():assert sha((ROOT/'qa/fixtures'/kind/path).read_bytes())==record['sha256'];checked+=1
 for origin in json.loads((ROOT/'qa/fixtures/host/exports/origins.json').read_text()):
  assert sha((ROOT/origin['exportFile']).read_bytes())==origin['fragmentSha256'];checked+=1
 icon=json.loads((ROOT/'qa/icon-provenance.json').read_text());assert sha((ROOT/'assets/extension_icon.png').read_bytes())==icon['sha256'];assert (ROOT/'assets/extension_icon.png').read_bytes()==(ROOT.parent/'assets/extension_icon.png').read_bytes();checked+=1
 print('V1 + exact immutable fixtures/icon:',checked,'hash checks passed')
if __name__=='__main__':verify()

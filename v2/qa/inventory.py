"""Worktree-candidate inventory, deliberately not a staged-blob verification."""
from pathlib import Path
import subprocess,json,hashlib,stat
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parent;DEST=ROOT/'qa/candidate-inventory.json'
def collect():
 raw=subprocess.check_output(['git','ls-files','-c','-o','--exclude-standard','-z','--','README.md','v2'],cwd=REPO)
 paths=sorted(set(p.decode() for p in raw.split(b'\0') if p));records={}
 for name in paths:
  p=REPO/name
  if p==DEST:continue
  assert not p.is_symlink() and p.is_file(),name
  assert name=='README.md' or name.startswith('v2/'),name
  records[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'mode':oct(stat.S_IMODE(p.stat().st_mode)),'bytes':p.stat().st_size}
 ignored=subprocess.check_output(['git','ls-files','--others','--ignored','--exclude-standard','-z','--','v2'],cwd=REPO).split(b'\0')
 bad=[p.decode() for p in ignored if p and not p.startswith((b'v2/.work/',b'v2/qa/schema/node_modules/'))];assert not bad,bad
 tracked=subprocess.check_output(['git','diff','--name-only','-z'],cwd=REPO).split(b'\0');assert all(not p or p==b'README.md' or p.startswith(b'v2/') for p in tracked)
 assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=REPO),'Index must remain empty'
 return records
if __name__=='__main__':
 import sys
 records=collect()
 if '--check'in sys.argv:assert json.loads(DEST.read_text())['files']==records,'Inventory stale'
 else:DEST.write_text(json.dumps({'scope':'All Git-visible README.md and v2 candidates except this inventory; worktree bytes only, not staged blobs. Parent must rehash staged blobs before commit.','files':records},indent=2)+'\n')
 print('Candidate inventory:',len(records),'files; index empty; no unexpected ignored durable files')

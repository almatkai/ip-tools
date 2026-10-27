import json,subprocess,pathlib,sys
from corpus import corpus
root=pathlib.Path(__file__).resolve().parents[1]
cases=corpus()
p=subprocess.run(['node',str(root/'qa/oracle.cjs')],input=json.dumps(cases),text=True,capture_output=True,check=True)
expected=[json.loads(s) for s in p.stdout.splitlines()]
(root/'.work/corpus.json').write_text(json.dumps(cases))
(root/'.work/oracle.json').write_text(json.dumps(expected))
print('actual-source oracle vectors:',len(expected),'; throwing:',sum('error' in x for x in expected))

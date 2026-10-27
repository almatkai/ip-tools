from pathlib import Path
import difflib
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'qa/fixtures/host';out=ROOT/'.work/host-patched';out.mkdir(parents=True,exist_ok=True)
paths=['src/renderer/ExtensionRuntimeView.tsx','src/renderer/src/raycast-api/list-runtime.tsx','src/shared/extensionRuntime.ts']
patch=[]
for path in paths:
 old=(base/path).read_text();s=old
 if 'ExtensionRuntimeView' in path:
  start=s.index('  const [state, setState]', s.index('export default function ExtensionRuntimeView'))
  end=s.index('\n  return (', start)
  s=s[:start]+(ROOT/'qa/host-view-body.ts.inc').read_text()+s[end:]
  start=s.index('            onInvokeAction={async (actionId, formValues) => {', start)
  end=s.index('\n          />', start)
  s=s[:start]+'            onInvokeAction={handleInvokeAction}'+s[end:]
  s=s.replace('              setState(fromRunResult(next))', '''              currentSession.current = `${next.sessionId}:${next.generation ?? ''}`
              searchRequestSeq.current += 1
              inputPending.current = null
              draft.current = { revision: 0, acknowledged: 0, query: next.root.props?.searchText,
                choice: next.root.props?.__clientChoice }
              setSeed(next)
              setActionNotice(null)
              setState(fromRunResult(next))''')
  s=s.replace('<Message tone="error">{error}</Message>', '<Message tone="error">{error}</Message>\n          <Button variant="quiet" onClick={() => void readOnly()}>Refresh</Button>')
  s=s.replace('          <ExtensionRuntimeSurface\n', '          <ExtensionRuntimeSurface\n            key={sessionOwner}\n')
 elif path.endswith('list-runtime.tsx'):
  s=s.replace("    if (typeof root.props?.searchText === 'string') {\n      setQuery", "    if (!hasServerSearch && typeof root.props?.searchText === 'string') {\n      setQuery")
  s=s.replace('  }, [root.props?.searchText])', '  }, [root.props?.searchText, hasServerSearch])')
  s=s.replace("    if (query === lastSentQuery.current) return", "    if (hasServerSearch || query === lastSentQuery.current) return")
  s=s.replace('  }, [query, onSearchTextChanged])','  }, [query, onSearchTextChanged, hasServerSearch])')
  s=s.replace('                  setQuery(event.target.value)\n                  setSelected(0)', "                  const next = event.target.value\n                  setQuery(next)\n                  setSelected(0)\n                  if (hasServerSearch) {\n                    lastSentQuery.current = next\n                    void onSearchTextChanged(next)\n                  }")
  s=s.replace("      title: typeof candidate.props?.title === 'string' ? candidate.props.title : 'No results',", "      title: typeof candidate.props?.title === 'string' ? candidate.props.title : 'No results',\n      icon: parseRowIcon(candidate.props?.icon),")
  s=s.replace("    : hasQuery\n      ? 'No matching applications'", "    : hasServerSearch\n      ? (root.props?.isLoading === true ? 'Loading…' : emptyView?.title || 'No results')\n      : hasQuery\n      ? 'No matching applications'")
  s=s.replace('            <div>\n              <p className="text-[13px] text-ink-2">', '            <div>\n              {emptyView?.icon ? <RowIcon row={{ id: \'empty\', title: emptyTitle, icon: emptyView.icon }} /> : null}\n              <p className="text-[13px] text-ink-2">')
  s=s.replace('    setAccessoryValue((current) => {', "    const restored = (root.props?.searchBarAccessory as ExtensionRuntimeNode | undefined)?.props?.value\n    setAccessoryValue((current) => {\n      if (typeof restored === 'string' && searchAccessory?.options.some((option) => option.value === restored)) return restored")
 else:
  for name in ['ExtensionInvokeActionResult','ExtensionSearchTextChangedResult']:
   s=s.replace('export type '+name+' =\n',"export type "+name+" =\n  | { ok: true; mode: 'unchanged' }\n")
 p=out/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 patch.extend(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='a/'+path,tofile='b/'+path))
(ROOT/'integration/renderer-ownership.patch').write_text(''.join(patch))
print('Prepared unapplied renderer patch; pinned host unchanged')

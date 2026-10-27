  const [seed, setSeed] = useState(initial)
  const [state, setState] = useState<RuntimeViewState>(() => fromRunResult(initial))
  const [error, setError] = useState<string | null>(null)
  const [actionNotice, setActionNotice] = useState<ActionNotice | null>(null)
  const sessionOwner = `${seed.sessionId}:${seed.generation ?? ''}`
  const currentSession = useRef<string | null>(sessionOwner)
  const searchRequestSeq = useRef(0)
  const inputPending = useRef<number | null>(null)
  const draft = useRef({ revision: 0, acknowledged: 0, query: initial.root.props?.searchText,
    choice: initial.root.props?.__clientChoice })
  const latestState = useRef(state)
  latestState.current = state
  const disposeTimerRef = useRef<{ sessionId: string; timer: number } | null>(null)
  const actionNoticeTimerRef = useRef<number | null>(null)
  const isFormSurface = state.root.type.startsWith('Form')
  const showActionNotice = useCallback((message: string, persist = false): void => {
    if (actionNoticeTimerRef.current !== null) window.clearTimeout(actionNoticeTimerRef.current)
    actionNoticeTimerRef.current = null
    setActionNotice({ message, tone: /could not|failed|failure|error|unknown|uncertain/i.test(message) ? 'error' : 'success' })
    if (!persist) actionNoticeTimerRef.current = window.setTimeout(() => {
      actionNoticeTimerRef.current = null
      setActionNotice(null)
    }, 2400)
  }, [])
  useEffect(() => {
    currentSession.current = `${initial.sessionId}:${initial.generation ?? ''}`
    setSeed(initial)
    searchRequestSeq.current += 1
    inputPending.current = null
    draft.current = { revision: 0, acknowledged: 0, query: initial.root.props?.searchText,
      choice: initial.root.props?.__clientChoice }
    setState(fromRunResult(initial))
    setError(null)
    setActionNotice(null)
    return () => {
      currentSession.current = null
      searchRequestSeq.current += 1
      inputPending.current = null
      if (actionNoticeTimerRef.current !== null) window.clearTimeout(actionNoticeTimerRef.current)
    }
  }, [initial.sessionId, initial.generation])
  useEffect(() => {
    const pending = disposeTimerRef.current
    if (pending?.sessionId === state.sessionId) {
      window.clearTimeout(pending.timer)
      disposeTimerRef.current = null
    }
    return () => {
      const sessionId = state.sessionId
      const timer = window.setTimeout(() => {
        if (disposeTimerRef.current?.timer === timer) disposeTimerRef.current = null
        void window.tezbar.extensionDisposeSession({ sessionId })
      }, 0)
      disposeTimerRef.current = { sessionId, timer }
    }
  }, [state.sessionId])

  // A model epoch is never a client input revision. Read-only recovery may
  // acknowledge only the exact complete draft, never merely clear a busy flag.
  const acceptView = (result: Extract<ExtensionRunCommandResult, { ok: true; mode: 'view' }>, inputReply = false): boolean => {
    if (result.sessionId !== seed.sessionId || result.generation !== seed.generation) return false
    const atomic = typeof latestState.current.root.props?.__clientInputAction === 'string'
    if (atomic && result.root.props?.__clientRevision !== draft.current.revision) return false
    if (!atomic && !inputReply && draft.current.revision > draft.current.acknowledged) return false
    draft.current.acknowledged = draft.current.revision
    setState(fromRunResult(result))
    setError(null)
    return true
  }
  const readOnly = async (loadMore = false): Promise<void> => {
    if (currentSession.current !== sessionOwner || inputPending.current !== null) return
    const seq = ++searchRequestSeq.current
    try {
      const result = await (loadMore ? window.tezbar.extensionLoadMore : window.tezbar.extensionRefreshSession)({ sessionId: seed.sessionId })
      if (currentSession.current !== sessionOwner || seq !== searchRequestSeq.current) return
      if (!result.ok) { setError(result.message); return }
      if (result.mode === 'view') acceptView(result)
    } catch (error) {
      if (currentSession.current === sessionOwner && seq === searchRequestSeq.current)
        setError(error instanceof Error ? error.message : String(error))
    }
  }
  useEffect(() => {
    const stop = startSessionRefresh({ sessionId: state.sessionId, generation: state.generation,
      refreshMs: state.refreshMs, subscribe: window.tezbar.onExtensionSessionInvalidated,
      subscribeVisibility: window.tezbar.onWindowVisibility, refresh: () => readOnly() })
    return stop
  }, [state.sessionId, state.generation, state.refreshMs, sessionOwner])

  const sendInput = async (change: { query?: unknown; choice?: unknown }): Promise<void> => {
    if (currentSession.current !== sessionOwner) return
    if (draft.current.revision >= Number.MAX_SAFE_INTEGER) { setError('Input revision limit reached; reopen session'); return }
    const revision = ++draft.current.revision
    if (Object.hasOwn(change, 'query')) draft.current.query = change.query
    if (Object.hasOwn(change, 'choice')) draft.current.choice = change.choice
    const seq = ++searchRequestSeq.current
    inputPending.current = revision
    setError(null)
    setActionNotice(null)
    if (actionNoticeTimerRef.current !== null) window.clearTimeout(actionNoticeTimerRef.current)
    // Revoke visible stale rows immediately. Query/choice remain client owned
    // even if this request fails, is unchanged, or completes out of order.
    setState(prev => ({ ...prev, actions: prev.actions.filter(a => a.id.startsWith('control:')),
      root: { ...prev.root, children: [], props: { ...prev.root.props, isLoading: true, searchText: draft.current.query,
        searchBarAccessory: prev.root.props?.searchBarAccessory ? {
          ...(prev.root.props.searchBarAccessory as ExtensionRuntimeNode), props: {
            ...(prev.root.props.searchBarAccessory as ExtensionRuntimeNode).props, value: draft.current.choice }
        } : undefined } } }))
    const inputAction = latestState.current.root.props?.__clientInputAction
    try {
      const result = typeof inputAction === 'string'
        ? await window.tezbar.extensionInvokeAction({ sessionId: seed.sessionId, actionId: inputAction,
            formValues: { revision, searchText: draft.current.query, value: draft.current.choice } })
        : await window.tezbar.extensionSearchTextChanged({ sessionId: seed.sessionId, searchText: String(draft.current.query ?? '') })
      if (currentSession.current !== sessionOwner || seq !== searchRequestSeq.current) return
      if (!result.ok) { setError(result.message); return }
      if (result.mode !== 'view' || !acceptView(result, true))
        setError('Input was not acknowledged. Refresh or enter a new value.')
    } catch (error) {
      if (currentSession.current === sessionOwner && seq === searchRequestSeq.current)
        setError(error instanceof Error ? error.message : String(error))
    } finally {
      if (currentSession.current === sessionOwner && inputPending.current === revision) {
        inputPending.current = null
        if (draft.current.acknowledged !== revision) setState(prev => ({ ...prev,
          root: { ...prev.root, props: { ...prev.root.props, isLoading: false } } }))
      }
    }
  }
  const handleSearchTextChanged = (searchText: string): Promise<void> => sendInput({ query: searchText })
  const handleLoadMore = (): Promise<void> => readOnly(true)
  const handleInvokeAction = async (actionId: string, formValues?: Record<string, unknown>): Promise<void> => {
    if (currentSession.current !== sessionOwner) return
    if (formValues && Object.hasOwn(formValues, 'value') && latestState.current.root.props?.__clientInputAction) {
      const accessory = latestState.current.root.props?.searchBarAccessory as ExtensionRuntimeNode | undefined
      if (accessory?.props?.actionId !== actionId) return
      await sendInput({ choice: formValues.value })
      return
    }
    if (inputPending.current !== null || draft.current.acknowledged !== draft.current.revision) return
    const invokedAction = latestState.current.actions.find(action => action.id === actionId)
    if (!invokedAction) return
    const seq = ++searchRequestSeq.current
    setError(null)
    try {
      const result = await window.tezbar.extensionInvokeAction({ sessionId: seed.sessionId, actionId, formValues })
      if (currentSession.current !== sessionOwner || seq !== searchRequestSeq.current) return
      if (!result.ok) { setError(result.message); showActionNotice(`Failed · ${result.message}`, isFormSurface); return }
      if (result.mode === 'unchanged') return
      if (result.mode === 'view' && !acceptView(result)) return
      const notice = effectNotice(result.effects)
      const message = notice?.message || result.message?.trim() || fallbackActionNotice(invokedAction)
      if (message) showActionNotice(message, isFormSurface)
    } catch (error) {
      if (currentSession.current === sessionOwner && seq === searchRequestSeq.current)
        setError(error instanceof Error ? error.message : String(error))
    }
  }

import React, { useEffect, useMemo, useRef, useState } from 'react'

const API = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'

async function api<T>(path: string, params?: Record<string, string | number>) {
  const url = new URL(`/api/${path}`, API)
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)))
  const r = await fetch(url.toString())
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  const j = await r.json().catch(() => ({}))
  const data = (j && (j.data ?? j.results ?? j)) as T
  return data
}

type TagItem = { name: string; count: number }

type Chunk = {
  chunk_id: string
  message_id?: string
  chat_id?: string
  content?: string
  similarity?: number
  similarity_score?: number
}

type TagMessage = {
  content?: string
  message_id?: string
  chat_id?: string
  role?: string
  timestamp?: string
  tags?: string[]
}

function Section(props: { title: string; children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <section style={{ border: '1px solid #1f2937', padding: 8, borderRadius: 6 }}>
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
        <div style={{ color: '#93c5fd' }}>{props.title}</div>
        {props.right}
      </header>
      {props.children}
    </section>
  )
}

function Row({ children }: { children: React.ReactNode }) {
  return <div style={{ borderBottom: '1px dashed #1f2937', paddingBottom: 6, marginBottom: 6 }}>{children}</div>
}

function ChatView({ chatId }: { chatId: string }) {
  const [messages, setMessages] = useState<Array<{ id: string; content?: string; role?: string; timestamp?: string }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    document.title = `Chat ${chatId} — ChatMind`
  }, [chatId])

  useEffect(() => {
    const run = async () => {
      setLoading(true); setError(null)
      try {
        const data = await api<typeof messages>(`chats/${encodeURIComponent(chatId)}/messages`, { limit: 200 })
        setMessages(Array.isArray(data) ? data : [])
      } catch (e: any) {
        setError(e?.message || 'Failed to load chat')
      } finally {
        setLoading(false)
      }
    }
    run()
  }, [chatId])

  return (
    <div style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace', color: '#e5e7eb', background: '#0b1220', minHeight: '100vh' }}>
      <div style={{ padding: 12, borderBottom: '1px solid #1f2937', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ color: '#a7f3d0' }}>$ chat {chatId}</div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => navigator.clipboard.writeText(chatId)} style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '4px 8px', borderRadius: 4 }}>copy chat_id</button>
          <a href="/" style={{ color: '#9ca3af', textDecoration: 'none', border: '1px solid #374151', padding: '4px 8px', borderRadius: 4 }}>back</a>
        </div>
      </div>
      <div style={{ padding: 12 }}>
        {loading && <div>loading…</div>}
        {error && <div style={{ color: '#fca5a5' }}>{error}</div>}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxWidth: 900, margin: '0 auto' }}>
          {messages.map((m, i) => (
            <div key={m.id || i} style={{ border: '1px solid #1f2937', borderRadius: 6, overflow: 'hidden' }}>
              <div style={{ background: '#0f172a', padding: 6, color: '#9ca3af', fontSize: 12, display: 'flex', justifyContent: 'space-between' }}>
                <span>{m.role || 'message'}</span>
                {m.timestamp && <span>{new Date(m.timestamp).toLocaleString()}</span>}
              </div>
              <div style={{ padding: 10, color: '#e5e7eb', whiteSpace: 'pre-wrap' }}>{m.content}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function App() {
  // URL param routing: if chat_id is present, render ChatView
  const params = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : new URLSearchParams()
  const chatViewId = params.get('chat_id') || undefined
  if (chatViewId) return <ChatView chatId={chatViewId} />

  // inputs
  const [query, setQuery] = useState('')
  const [limit, setLimit] = useState(10)
  const [clusterId, setClusterId] = useState('')

  // refs for focusing
  const searchInputRef = useRef<HTMLInputElement>(null)
  const clusterInputRef = useRef<HTMLInputElement>(null)

  // data state
  const [tags, setTags] = useState<TagItem[]>([])
  const [tagsLoading, setTagsLoading] = useState(false)
  const [tagsError, setTagsError] = useState<string | null>(null)
  const [selectedTag, setSelectedTag] = useState<string | null>(null)
  const [tagMessages, setTagMessages] = useState<TagMessage[]>([])
  const [tagMessagesLoading, setTagMessagesLoading] = useState(false)
  const [tagMessagesError, setTagMessagesError] = useState<string | null>(null)
  const [tagMsgExpanded, setTagMsgExpanded] = useState<Record<string, boolean>>({})

  const [searchResults, setSearchResults] = useState<Chunk[]>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [searchExpanded, setSearchExpanded] = useState<Record<number, boolean>>({})
  const [searchSelectedIdx, setSearchSelectedIdx] = useState(0)

  const [clusterChunks, setClusterChunks] = useState<Chunk[]>([])
  const [related, setRelated] = useState<Chunk[]>([])
  const [clusterLoading, setClusterLoading] = useState(false)
  const [clusterError, setClusterError] = useState<string | null>(null)
  const [chunkExpanded, setChunkExpanded] = useState<Record<string, boolean>>({})
  const [relatedExpanded, setRelatedExpanded] = useState<Record<string, boolean>>({})

  // persistence
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('cm_minimal_state') || '{}')
      if (saved.query) setQuery(saved.query)
      if (saved.limit) setLimit(saved.limit)
      if (saved.clusterId) setClusterId(saved.clusterId)
    } catch {}
  }, [])
  useEffect(() => { runTags().catch(() => {}) }, [])
  useEffect(() => {
    const state = { query, limit, clusterId }
    try { localStorage.setItem('cm_minimal_state', JSON.stringify(state)) } catch {}
  }, [query, limit, clusterId])

  // helpers
  const copy = async (text: string) => {
    try { await navigator.clipboard.writeText(text) } catch {}
  }

  // actions
  const runTags = async () => {
    setTagsLoading(true); setTagsError(null)
    try {
      const data = await api<TagItem[]>('search/tags/available')
      setTags(Array.isArray(data) ? data : [])
    } catch (e: any) {
      setTagsError(e?.message || 'Failed to load tags')
    } finally {
      setTagsLoading(false)
    }
  }

  const runTagMessages = async (tagName: string) => {
    setSelectedTag(tagName)
    setTagMessages([]); setTagMessagesError(null); setTagMessagesLoading(true)
    try {
      const data = await api<TagMessage[]>('search/tags', { tags: tagName, limit })
      setTagMessages(Array.isArray(data) ? data : [])
      setTagMsgExpanded({})
    } catch (e: any) {
      setTagMessagesError(e?.message || 'Failed to load messages for tag')
    } finally {
      setTagMessagesLoading(false)
    }
  }

  const runSearch = async () => {
    setSearchLoading(true); setSearchError(null); setSearchSelectedIdx(0)
    try {
      const data = query ? await api<Chunk[]>('search/semantic', { query, limit }) : []
      setSearchResults(Array.isArray(data) ? data : [])
      setSearchExpanded({})
    } catch (e: any) {
      setSearchError(e?.message || 'Search failed')
    } finally {
      setSearchLoading(false)
    }
  }

  const runCluster = async () => {
    setClusterLoading(true); setClusterError(null)
    try {
      const chunks = clusterId ? await api<Chunk[]>('chunks', { cluster_id: clusterId, limit }) : []
      setClusterChunks(Array.isArray(chunks) ? chunks : [])
      setRelated([])
      setChunkExpanded({})
      setRelatedExpanded({})
      if (chunks && chunks.length) {
        const first = chunks[0]
        const sim = await api<Chunk[]>(`search/similar/${encodeURIComponent(first.chunk_id)}`, { limit })
        setRelated(Array.isArray(sim) ? sim : [])
      }
    } catch (e: any) {
      setClusterError(e?.message || 'Cluster lookup failed')
    } finally {
      setClusterLoading(false)
    }
  }

  // keyboard shortcuts
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === '/' && !e.metaKey && !e.ctrlKey) {
        e.preventDefault(); searchInputRef.current?.focus(); return
      }
      if (e.key.toLowerCase() === 't' && !e.metaKey && !e.ctrlKey) { clusterInputRef.current?.focus(); return }
      if (e.key.toLowerCase() === 'c' && !e.metaKey && !e.ctrlKey) { clusterInputRef.current?.focus(); return }
      if (['j', 'k'].includes(e.key) && document.activeElement === document.body) {
        if (searchResults.length) {
          e.preventDefault()
          setSearchSelectedIdx((idx) => {
            const next = e.key === 'j' ? Math.min(idx + 1, searchResults.length - 1) : Math.max(idx - 1, 0)
            return next
          })
        }
      }
      if (e.key === 'Enter' && document.activeElement === document.body && searchResults.length) {
        e.preventDefault()
        setSearchExpanded((m) => ({ ...m, [searchSelectedIdx]: !m[searchSelectedIdx] }))
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [searchResults.length])

  // UI helpers
  const sim = (c: Chunk) => (c.similarity_score ?? c.similarity ?? 0) as number

  const headerHelp = (
    <div style={{ color: '#9ca3af', fontSize: 12 }}>
      keys: <b>/</b> focus search, <b>t</b> tags, <b>c</b> cluster, <b>j/k</b> select, <b>Enter</b> toggle
    </div>
  )

  return (
    <div style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace', color: '#e5e7eb', background: '#0b1220', minHeight: '100vh', padding: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <div style={{ color: '#a7f3d0' }}>$ chatmind ui — minimal</div>
        {headerHelp}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
        {/* Tags */}
        <Section title="$ tags ls" right={<button onClick={runTags} style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '4px 8px', borderRadius: 4 }}>fetch</button>}>
          {tagsLoading && <div>loading…</div>}
          {tagsError && <div style={{ color: '#fca5a5' }}>{tagsError}</div>}
          <div style={{ marginTop: 4, maxHeight: 180, overflow: 'auto' }}>
            {tags.map(t => (
              <button key={t.name} onClick={() => runTagMessages(t.name)} style={{ display: 'flex', justifyContent: 'space-between', width: '100%', textAlign: 'left', background: 'transparent', border: 'none', color: '#e5e7eb', borderBottom: '1px dashed #1f2937', padding: '2px 0' }}>
                <span style={{ color: selectedTag === t.name ? '#fbbf24' : undefined }}>#{t.name}</span>
                <span>{t.count}</span>
              </button>
            ))}
            {!tagsLoading && !tagsError && tags.length === 0 && <div style={{ color: '#9ca3af' }}>no tags</div>}
          </div>
          {/* Tag messages below */}
          <div style={{ marginTop: 8 }}>
            <div style={{ color: '#9ca3af', marginBottom: 4, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span>{selectedTag ? `$ tag ${selectedTag} — messages` : 'select a tag'}</span>
              {selectedTag && <span style={{ fontSize: 12, color: '#9ca3af' }}>{tagMessages.length}</span>}
            </div>
            {tagMessagesLoading && <div>loading…</div>}
            {tagMessagesError && <div style={{ color: '#fca5a5' }}>{tagMessagesError}</div>}
            <div style={{ maxHeight: 180, overflow: 'auto' }}>
              {tagMessages.map((m, i) => {
                const id = (m.message_id || 'm') + String(i)
                const firstLine = (m.content || '').split('\n')[0]
                const text = firstLine.length > 160 && !tagMsgExpanded[id] ? firstLine.slice(0, 160) + '…' : firstLine
                return (
                  <div key={id} style={{ borderBottom: '1px dashed #1f2937', paddingBottom: 6, marginBottom: 6 }}>
                    <div style={{ color: '#a7f3d0' }}>{text || '(empty)'}</div>
                    <div style={{ color: '#9ca3af', fontSize: 12, display: 'flex', gap: 10, marginTop: 4, flexWrap: 'wrap' }}>
                      <button onClick={() => setTagMsgExpanded(m => ({ ...m, [id]: !m[id] }))} style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '2px 6px', borderRadius: 4 }}>{tagMsgExpanded[id] ? 'collapse' : 'expand'}</button>
                      {m.content && <button onClick={() => copy(m.content!)} style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '2px 6px', borderRadius: 4 }}>copy text</button>}
                      {m.chat_id && <button onClick={() => window.open(`/?chat_id=${encodeURIComponent(m.chat_id!)}`, '_blank', 'noopener,noreferrer')} style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '2px 6px', borderRadius: 4 }}>go to chat</button>}
                    </div>
                  </div>
                )
              })}
              {!tagMessagesLoading && selectedTag && tagMessages.length === 0 && <div style={{ color: '#9ca3af' }}>no messages</div>}
            </div>
          </div>
        </Section>

        {/* Semantic search */}
        <Section title={`$ search "${query || '...'}"`} right={<span style={{ color: '#9ca3af', fontSize: 12 }}>{searchResults.length} results</span>}>
          <div style={{ display: 'flex', gap: 6 }}>
            <input ref={searchInputRef} value={query} onChange={e => setQuery(e.target.value)} placeholder="query" onKeyDown={e => e.key === 'Enter' && runSearch()} style={{ flex: 1, background: '#0b1220', border: '1px solid #374151', color: '#e5e7eb', padding: 6, borderRadius: 4 }} />
            <input type="number" value={limit} onChange={e => setLimit(parseInt(e.target.value || '10'))} onKeyDown={e => e.key === 'Enter' && runSearch()} style={{ width: 72, background: '#0b1220', border: '1px solid #374151', color: '#e5e7eb', padding: 6, borderRadius: 4 }} />
            <button onClick={runSearch} style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '4px 8px', borderRadius: 4 }}>go</button>
          </div>
          {searchLoading && <div style={{ marginTop: 6 }}>searching…</div>}
          {searchError && <div style={{ color: '#fca5a5', marginTop: 6 }}>{searchError}</div>}
          <div style={{ marginTop: 8, maxHeight: 380, overflow: 'auto' }}>
            {searchResults.map((r, i) => {
              const isSelected = i === searchSelectedIdx
              const isExpanded = !!searchExpanded[i]
              const score = sim(r)
              return (
                <Row key={i}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <button onClick={() => setSearchExpanded(m => ({ ...m, [i]: !m[i] }))} title="toggle" style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '2px 6px', borderRadius: 4 }}> {isExpanded ? '−' : '+'} </button>
                    <div style={{ color: isSelected ? '#fbbf24' : '#a7f3d0', flex: 1 }}>{(r.content || '').slice(0, isExpanded ? 9999 : 160)}</div>
                  </div>
                  <div style={{ color: '#9ca3af', fontSize: 12, display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 4 }}>
                    <span>chat:{r.chat_id}</span>
                    <span>msg:{r.message_id}</span>
                    <span>sim:{typeof score === 'number' ? score.toFixed(3) : score}</span>
                    {r.chunk_id && <button onClick={() => copy(r.chunk_id!)} style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '2px 6px', borderRadius: 4 }}>copy chunk_id</button>}
                    {r.chat_id && <button onClick={() => window.open(`/?chat_id=${encodeURIComponent(r.chat_id!)}`, '_blank', 'noopener,noreferrer')} style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '2px 6px', borderRadius: 4 }}>go to chat</button>}
                  </div>
                </Row>
              )
            })}
            {!searchLoading && !searchError && searchResults.length === 0 && <div style={{ color: '#9ca3af' }}>no results</div>}
          </div>
        </Section>

        {/* Cluster → chunks → related */}
        <Section title={`$ cluster ${clusterId || '[id]'} | chunks && similar`} right={<span style={{ color: '#9ca3af', fontSize: 12 }}>{clusterChunks.length}/{related.length}</span>}>
          <div style={{ display: 'flex', gap: 6 }}>
            <input ref={clusterInputRef} value={clusterId} onChange={e => setClusterId(e.target.value)} placeholder="cluster_id" onKeyDown={e => e.key === 'Enter' && runCluster()} style={{ flex: 1, background: '#0b1220', border: '1px solid #374151', color: '#e5e7eb', padding: 6, borderRadius: 4 }} />
            <input type="number" value={limit} onChange={e => setLimit(parseInt(e.target.value || '10'))} onKeyDown={e => e.key === 'Enter' && runCluster()} style={{ width: 72, background: '#0b1220', border: '1px solid #374151', color: '#e5e7eb', padding: 6, borderRadius: 4 }} />
            <button onClick={runCluster} style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '4px 8px', borderRadius: 4 }}>go</button>
          </div>
          {clusterLoading && <div style={{ marginTop: 6 }}>loading…</div>}
          {clusterError && <div style={{ color: '#fca5a5', marginTop: 6 }}>{clusterError}</div>}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 8 }}>
            <div>
              <div style={{ color: '#fcd34d', marginBottom: 6 }}># chunks</div>
              <div style={{ maxHeight: 340, overflow: 'auto' }}>
                {clusterChunks.map((c, i) => (
                  <Row key={c.chunk_id || i.toString()}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <button onClick={() => setChunkExpanded(m => ({ ...m, [c.chunk_id]: !m[c.chunk_id] }))} title="toggle" style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '2px 6px', borderRadius: 4 }}> {chunkExpanded[c.chunk_id] ? '−' : '+'} </button>
                      <div style={{ color: '#a7f3d0', flex: 1 }}>{(c.content || '').slice(0, chunkExpanded[c.chunk_id] ? 9999 : 160)}</div>
                    </div>
                    <div style={{ color: '#9ca3af', fontSize: 12, display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 4 }}>
                      <span>chunk:{c.chunk_id}</span>
                      <span>msg:{c.message_id}</span>
                      <button onClick={() => copy(c.chunk_id)} style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '2px 6px', borderRadius: 4 }}>copy chunk_id</button>
                      {c.chat_id && <button onClick={() => window.open(`/?chat_id=${encodeURIComponent(c.chat_id!)}`, '_blank', 'noopener,noreferrer')} style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '2px 6px', borderRadius: 4 }}>go to chat</button>}
                    </div>
                  </Row>
                ))}
                {!clusterLoading && clusterChunks.length === 0 && <div style={{ color: '#9ca3af' }}>no chunks</div>}
              </div>
            </div>
            <div>
              <div style={{ color: '#fcd34d', marginBottom: 6 }}># related</div>
              <div style={{ maxHeight: 340, overflow: 'auto' }}>
                {related.map((c, i) => (
                  <Row key={(c.chunk_id || 'r') + i}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <button onClick={() => setRelatedExpanded(m => ({ ...m, [c.chunk_id]: !m[c.chunk_id] }))} title="toggle" style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '2px 6px', borderRadius: 4 }}> {relatedExpanded[c.chunk_id] ? '−' : '+'} </button>
                      <div style={{ color: '#a7f3d0', flex: 1 }}>{(c.content || '').slice(0, relatedExpanded[c.chunk_id] ? 9999 : 160)}</div>
                    </div>
                    <div style={{ color: '#9ca3af', fontSize: 12, display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 4 }}>
                      <span>chunk:{c.chunk_id}</span>
                      <span>msg:{c.message_id}</span>
                      <span>sim:{typeof sim(c) === 'number' ? sim(c).toFixed(3) : sim(c)}</span>
                      <button onClick={() => copy(c.chunk_id)} style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '2px 6px', borderRadius: 4 }}>copy chunk_id</button>
                      {c.chat_id && <button onClick={() => window.open(`/?chat_id=${encodeURIComponent(c.chat_id!)}`, '_blank', 'noopener,noreferrer')} style={{ background: '#111827', border: '1px solid #374151', color: '#9ca3af', padding: '2px 6px', borderRadius: 4 }}>go to chat</button>}
                    </div>
                  </Row>
                ))}
                {!clusterLoading && related.length === 0 && <div style={{ color: '#9ca3af' }}>no related</div>}
              </div>
            </div>
          </div>
        </Section>
      </div>
    </div>
  )
} 
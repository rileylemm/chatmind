import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getSearchStats, getBridges, getSerendipity, getGraphVisualization, explainPath } from '../services/api';
import type { GraphData as VizGraphData } from '../services/api';
import { GraphView } from '../components/graph/GraphView';

const Cockpit: React.FC = () => {
  const { data: stats } = useQuery({ queryKey: ['stats'], queryFn: getSearchStats });
  const { data: bridges } = useQuery({ queryKey: ['bridges'], queryFn: () => getBridges({ limit: 10 }) });
  const { data: viz } = useQuery<VizGraphData>({ queryKey: ['viz'], queryFn: () => getGraphVisualization({ node_types: ['Chat', 'Cluster'], include_edges: true, limit: 200 }) });

  const seedId = bridges?.items?.[0]?.chat_id || '';
  const [novelty, setNovelty] = useState<number>(0.7);
  const { data: serendipity } = useQuery({
    queryKey: ['serendipity', seedId, novelty],
    queryFn: () => getSerendipity({ seed_id: seedId, type: 'chat', novelty, limit: 12 }),
    enabled: !!seedId,
  });

  const bridgePairs = useMemo(() => {
    // Build simple adjacent pairs from top bridges for demo explain
    const items = bridges?.items || [];
    const pairs: Array<{ a: string; b: string; titleA: string; titleB: string }> = [];
    for (let i = 0; i + 1 < items.length; i += 2) {
      pairs.push({ a: items[i].chat_id, b: items[i + 1].chat_id, titleA: items[i].title, titleB: items[i + 1].title });
    }
    return pairs;
  }, [bridges]);

  const handleExplain = async (a: string, b: string) => {
    try {
      const exp = await explainPath({ source_id: a, target_id: b });
      alert(`Path: ${exp.path_type}\nEvidence: ${exp.evidence.map((e) => e.type).join(', ') || 'none'}`);
    } catch {
      // ignore
    }
  };

  return (
    <div className="p-4 space-y-4">
      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-slate-900/50 text-white rounded p-4"><div className="text-xs opacity-70">Conversations</div><div className="text-2xl font-semibold">{stats?.total_conversations ?? '—'}</div></div>
        <div className="bg-slate-900/50 text-white rounded p-4"><div className="text-xs opacity-70">Messages</div><div className="text-2xl font-semibold">{stats?.total_messages ?? '—'}</div></div>
        <div className="bg-slate-900/50 text-white rounded p-4"><div className="text-xs opacity-70">Chunks</div><div className="text-2xl font-semibold">{stats?.total_chunks ?? '—'}</div></div>
        <div className="bg-slate-900/50 text-white rounded p-4"><div className="text-xs opacity-70">Hybrid</div><div className="text-2xl font-semibold">{stats?.neo4j_connected && stats?.qdrant_connected ? 'Online' : 'Degraded'}</div></div>
      </div>

      {/* Graph + Panels */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 bg-slate-900/30 rounded p-2">
          <div className="text-sm text-white/80 px-2 pb-2">Galaxy Map</div>
          <div className="h-[520px] bg-black/30 rounded">
            {viz ? <GraphView nodes={viz.nodes} edges={viz.edges} /> : <div className="h-full w-full flex items-center justify-center text-white/60">Loading map…</div>}
          </div>
        </div>
        <div className="col-span-1 space-y-4">
          {/* Bridges */}
          <div className="bg-slate-900/30 rounded p-3">
            <div className="text-sm text-white/80 pb-2">Bridges</div>
            <div className="space-y-2 max-h-72 overflow-auto">
              {bridges?.items?.map((b) => (
                <div key={b.chat_id} className="p-2 bg-slate-800/50 rounded text-white/80">
                  <div className="text-sm font-medium truncate">{b.title}</div>
                  <div className="text-xs opacity-70">Bridge score: {b.bridge_score} • Clusters: {b.clusters.slice(0, 3).join(', ')}</div>
                </div>
              )) || <div className="text-white/60">Loading…</div>}
            </div>
            {/* Quick Explain for top pair */}
            {bridgePairs.length > 0 && (
              <button onClick={() => handleExplain(bridgePairs[0].a, bridgePairs[0].b)} className="mt-2 w-full px-3 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-500 text-sm">Why are top bridges related?</button>
            )}
          </div>

          {/* Serendipity Reel */}
          <div className="bg-slate-900/30 rounded p-3">
            <div className="flex items-center justify-between pb-2">
              <div className="text-sm text-white/80">Serendipity</div>
              <div className="flex items-center gap-2 text-xs text-white/60">
                Novelty
                <input type="range" min={0} max={1} step={0.05} value={novelty} onChange={(e) => setNovelty(parseFloat(e.target.value))} />
                <span>{novelty.toFixed(2)}</span>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-2 max-h-72 overflow-auto">
              {serendipity?.items?.map((it, idx) => (
                <div key={idx} className="p-2 bg-slate-800/50 rounded text-white/80">
                  <div className="flex items-center justify-between text-xs opacity-70">
                    <div>combined {it.combined.toFixed(2)}</div>
                    <div>sim {it.similarity.toFixed(2)}</div>
                    <div>novel {it.novelty.toFixed(2)}</div>
                  </div>
                  <div className="text-sm truncate py-1">{it.content || '(no preview)'}</div>
                  <div className="flex gap-2 flex-wrap">
                    {(it.tags || []).slice(0, 6).map((t) => (
                      <span key={t} className="px-1.5 py-0.5 text-[10px] bg-slate-700/60 rounded">{t}</span>
                    ))}
                  </div>
                </div>
              )) || <div className="text-white/60">{seedId ? 'Loading…' : 'Waiting for seed…'}</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Cockpit; 
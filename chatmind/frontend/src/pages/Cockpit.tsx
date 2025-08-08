import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getSearchStats, getBridges, getSerendipity, getGraphVisualization } from '../services/api';
import type { GraphData as VizGraphData } from '../services/api';
import { GraphView } from '../components/graph/GraphView';

const Cockpit: React.FC = () => {
  const { data: stats } = useQuery({ queryKey: ['stats'], queryFn: getSearchStats });
  const { data: bridges } = useQuery({ queryKey: ['bridges'], queryFn: () => getBridges({ limit: 10 }) });
  const { data: viz } = useQuery<VizGraphData>({ queryKey: ['viz'], queryFn: () => getGraphVisualization({ node_types: ['Chat', 'Cluster'], include_edges: true, limit: 300 }) });

  // For serendipity, pick first chat from bridges as seed if available
  const seedId = bridges?.items?.[0]?.chat_id || '';
  const { data: serendipity } = useQuery({
    queryKey: ['serendipity', seedId],
    queryFn: () => getSerendipity({ seed_id: seedId, type: 'chat', novelty: 0.7, limit: 10 }),
    enabled: !!seedId,
  });

  return (
    <div className="p-4 space-y-4">
      {/* Top KPIs */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-slate-900/50 text-white rounded p-4">
          <div className="text-xs opacity-70">Conversations</div>
          <div className="text-2xl font-semibold">{stats?.total_conversations ?? '—'}</div>
        </div>
        <div className="bg-slate-900/50 text-white rounded p-4">
          <div className="text-xs opacity-70">Messages</div>
          <div className="text-2xl font-semibold">{stats?.total_messages ?? '—'}</div>
        </div>
        <div className="bg-slate-900/50 text-white rounded p-4">
          <div className="text-xs opacity-70">Chunks</div>
          <div className="text-2xl font-semibold">{stats?.total_chunks ?? '—'}</div>
        </div>
        <div className="bg-slate-900/50 text-white rounded p-4">
          <div className="text-xs opacity-70">Hybrid</div>
          <div className="text-2xl font-semibold">{stats?.neo4j_connected && stats?.qdrant_connected ? 'Online' : 'Degraded'}</div>
        </div>
      </div>

      {/* Middle: Graph + Panels */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 bg-slate-900/30 rounded p-2">
          <div className="text-sm text-white/80 px-2 pb-2">Galaxy Map</div>
          <div className="h-[520px] bg-black/30 rounded">
            {viz ? (
              <GraphView nodes={viz.nodes} edges={viz.edges} width={0} height={0} />
            ) : (
              <div className="h-full w-full flex items-center justify-center text-white/60">Loading map…</div>
            )}
          </div>
        </div>
        <div className="col-span-1 space-y-4">
          <div className="bg-slate-900/30 rounded p-3">
            <div className="text-sm text-white/80 pb-2">Bridges</div>
            <div className="space-y-2 max-h-64 overflow-auto">
              {bridges?.items?.map((b) => (
                <div key={b.chat_id} className="p-2 bg-slate-800/50 rounded text-white/80">
                  <div className="text-sm font-medium truncate">{b.title}</div>
                  <div className="text-xs opacity-70">Bridge score: {b.bridge_score} • Clusters: {b.clusters.slice(0, 3).join(', ')}</div>
                </div>
              )) || <div className="text-white/60">Loading…</div>}
            </div>
          </div>

          <div className="bg-slate-900/30 rounded p-3">
            <div className="text-sm text-white/80 pb-2">Serendipity</div>
            <div className="space-y-2 max-h-64 overflow-auto">
              {serendipity?.items?.map((it, idx) => (
                <div key={idx} className="p-2 bg-slate-800/50 rounded text-white/80">
                  <div className="text-xs opacity-70">combined {it.combined.toFixed(2)} | sim {it.similarity.toFixed(2)} | novel {it.novelty.toFixed(2)}</div>
                  <div className="text-sm truncate">{it.content || '(no preview)'} </div>
                </div>
              )) || <div className="text-white/60">Waiting for seed…</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Cockpit; 
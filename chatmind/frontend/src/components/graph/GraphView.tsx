import React, { useRef, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import type { GraphNode, GraphEdge } from '../../types';

type PositionedGraphNode = GraphNode & {
  x: number;
  y: number;
  type: string;
  name: string;
};

interface GraphViewProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  width?: number;
  height?: number;
  onNodeClick?: (node: GraphNode) => void;
  onNodeHover?: (node: GraphNode | null) => void;
  onZoomChange?: (zoom: number) => void;
}

export const GraphView: React.FC<GraphViewProps> = ({
  nodes,
  edges,
  width = 800,
  height = 600,
  onNodeClick,
  onNodeHover,
  onZoomChange,
}) => {
  // Reference to force graph API for freezing layout
  const fgRef = useRef<any>(null);
  // On mount, disable forces to lock UMAP positions
  useEffect(() => {
    if (fgRef.current) {
      fgRef.current.d3AlphaDecay(1);
      fgRef.current.d3VelocityDecay(1);
      fgRef.current.d3Force('charge', null);
    }
  }, []);
  // Transform data to match react-force-graph format
  const graphData = {
    nodes: nodes.map((n) => {
      let name = n.id;
      
      // Use appropriate title based on node type
      if (n.type === 'Chat' && n.properties.title) {
        name = n.properties.title;
      } else if (n.type === 'Topic' && n.properties.sample_titles && n.properties.sample_titles.length > 0) {
        name = n.properties.sample_titles[0]; // Use first sample title
      } else if (n.type === 'Message' && n.properties.content) {
        // For messages, use first 20 chars of content
        name = n.properties.content.substring(0, 20) + (n.properties.content.length > 20 ? '...' : '');
      }
      
      console.log(`Node ${n.id} (${n.type}): name="${name}", properties:`, n.properties);
      
      return {
        ...n,
        id: n.id,
        name: name,
      };
    }),
    links: edges.map((e) => ({
      source: e.source,
      target: e.target,
    })),
  };

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'Topic':
        return '#f59e0b';
      case 'Chat':
        return '#3b82f6';
      case 'Message':
        return '#10b981';
      default:
        return '#6b7280';
    }
  };

  const getNodeSize = (type: string, properties: Record<string, unknown> = {}) => {
    switch (type) {
      case 'Topic': {
        // Weighted size based on message count and recency
        const messageCount = (properties.message_count as number) || 0;
        const lastActive = (properties.last_active as number) || 0;
        const chatCount = (properties.chat_count as number) || 0;
        
        // Base size from message count
        let baseSize = Math.min(8 + (messageCount / 10), 25);
        
        // Boost for recent activity (within last 30 days)
        const thirtyDaysAgo = Date.now() / 1000 - (30 * 24 * 60 * 60);
        if (lastActive > thirtyDaysAgo) {
          baseSize *= 1.3; // 30% boost for recent activity
        }
        
        // Minimum size for topics with any content
        const finalSize = Math.max(baseSize, chatCount > 0 ? 12 : 8);
        console.log(`Topic size: ${finalSize} (messageCount: ${messageCount}, chatCount: ${chatCount})`);
        return finalSize;
      }
      case 'Chat': {
        const messageCount = (properties.message_count as number) || 0;
        const size = Math.min(6 + (messageCount / 5), 15);
        console.log(`Chat size: ${size} (messageCount: ${messageCount})`);
        return size;
      }
      case 'Message':
        return 4;   // Smallest
      default:
        return 6;
    }
  };

  return (
    <div className="relative">
      {/* Zoom Controls */}
      <div className="absolute top-4 right-4 z-10 flex flex-col space-y-2">
        <button
          onClick={() => {
            if (onZoomChange) onZoomChange(1.5);
          }}
          className="w-8 h-8 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center justify-center"
        >
          <span className="text-sm font-bold">+</span>
        </button>
        <button
          onClick={() => {
            if (onZoomChange) onZoomChange(0.5);
          }}
          className="w-8 h-8 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center justify-center"
        >
          <span className="text-sm font-bold">−</span>
        </button>
        <button
          onClick={() => {
            if (onZoomChange) onZoomChange(1);
          }}
          className="w-8 h-8 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center justify-center text-xs"
        >
          🏠
        </button>
      </div>
      
      <ForceGraph2D
        ref={fgRef}
        width={width}
        height={height}
        graphData={graphData}
        nodeLabel="name"
        nodeAutoColorBy="type"
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        nodeCanvasObject={(node: PositionedGraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
          const label = node.name;
          const fontSize = 12 / globalScale;
          const nodeSize = getNodeSize(node.type, node.properties);
          ctx.font = `${fontSize}px Inter`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillStyle = getNodeColor(node.type);
          ctx.beginPath();
          ctx.arc(node.x!, node.y!, nodeSize, 0, 2 * Math.PI);
          ctx.fill();
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 1;
          ctx.stroke();
          ctx.fillStyle = '#ffffff';
          ctx.fillText(label, node.x!, node.y! + nodeSize + 5);
        }}
        linkCanvasObject={(link: Record<string, unknown>, ctx: CanvasRenderingContext2D) => {
          // Calculate edge thickness based on similarity (if available)
          const thickness = (link.similarity as number) ? Math.max(1, (link.similarity as number) * 3) : 1;
          
          ctx.strokeStyle = '#666666';
          ctx.lineWidth = thickness;
          ctx.beginPath();
          ctx.moveTo((link.source as PositionedGraphNode).x!, (link.source as PositionedGraphNode).y!);
          ctx.lineTo((link.target as PositionedGraphNode).x!, (link.target as PositionedGraphNode).y!);
          ctx.stroke();
        }}
        onNodeClick={(node: PositionedGraphNode) => {
          console.log('Node clicked:', node);
          if (onNodeClick) onNodeClick(node);
        }}
        onNodeHover={(node: PositionedGraphNode | null) => {
          console.log('Node hover:', node);
          if (onNodeHover) onNodeHover(node);
        }}
      />
    </div>
  );
};
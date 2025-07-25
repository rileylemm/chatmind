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
  
  // On mount, previously tried to disable forces, but these methods are not available in latest react-force-graph-2d
  // useEffect(() => {
  //   if (fgRef.current) {
  //     fgRef.current.d3AlphaDecay(1);
  //     fgRef.current.d3VelocityDecay(1);
  //     fgRef.current.d3Force('charge', null);
  //   }
  // }, []);

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
      
      return {
        ...n,
        id: n.id,
        name: name,
      };
    }),
    links: edges.map((e) => ({
      source: e.source,
      target: e.target,
      type: e.type,
      properties: e.properties,
    })),
  };

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'Topic':
        return '#f59e0b'; // Orange
      case 'Chat':
        return '#3b82f6'; // Blue
      case 'Message':
        return '#10b981'; // Green
      default:
        return '#6b7280'; // Gray
    }
  };

  // Enhanced node sizing based on the mindmap plan formula
  const getNodeSize = (type: string, properties: Record<string, unknown> = {}) => {
    switch (type) {
              case 'Topic': {
          // Formula: log10(totalMessages + 1) * recencyBoost * importanceBoost
          const messageCount = (properties.message_count as number) || 0;
          const chatCount = (properties.chat_count as number) || 0;
          const lastActive = (properties.last_active as number) || 0;
          
          // Base size from log of message count
          const baseSize = Math.log10(messageCount + 1) * 8;
        
        // Recency boost (last 30 days = 1.2x, last 7 days = 1.4x)
        const thirtyDaysAgo = Date.now() / 1000 - (30 * 24 * 60 * 60);
        const sevenDaysAgo = Date.now() / 1000 - (7 * 24 * 60 * 60);
        
        let recencyBoost = 1.0;
        if (lastActive > sevenDaysAgo) {
          recencyBoost = 1.4;
        } else if (lastActive > thirtyDaysAgo) {
          recencyBoost = 1.2;
        }
        
        // Importance boost based on chat count and activity
        const importanceBoost = chatCount > 0 ? 1.3 : 1.0;
        
        const finalSize = Math.max(baseSize * recencyBoost * importanceBoost, 8);
        console.log(`Topic size: ${finalSize} (messageCount: ${messageCount}, recencyBoost: ${recencyBoost}, importanceBoost: ${importanceBoost})`);
        return finalSize;
      }
              case 'Chat': {
          const messageCount = (properties.message_count as number) || 0;
          const lastActive = (properties.create_time as number) || 0;
          
          // Base size from log of message count
          const baseSize = Math.log10(messageCount + 1) * 6;
        
        // Recency boost for chats
        const thirtyDaysAgo = Date.now() / 1000 - (30 * 24 * 60 * 60);
        const recencyBoost = lastActive > thirtyDaysAgo ? 1.2 : 1.0;
        
        const finalSize = Math.max(baseSize * recencyBoost, 4);
        console.log(`Chat size: ${finalSize} (messageCount: ${messageCount}, recencyBoost: ${recencyBoost})`);
        return finalSize;
      }
      case 'Message':
        return 3;   // Smallest, fixed size
      default:
        return 6;
    }
  };

  // Enhanced edge visualization with opacity scaling
  const getEdgeOpacity = (edge: Record<string, unknown>) => {
    // Base opacity
    let opacity = 0.3;
    
    // Increase opacity for stronger relationships
    if (edge.type === 'SUMMARIZES') {
      opacity = 0.6; // Topic-message relationships
    } else if (edge.type === 'HAS_TOPIC') {
      opacity = 0.5; // Chat-topic relationships
    } else if (edge.properties && typeof edge.properties === 'object' && 'weight' in edge.properties) {
      // Scale opacity by relationship weight
      opacity = Math.min(0.8, 0.3 + (edge.properties.weight as number) * 0.5);
    }
    
    return opacity;
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
          const fontSize = Math.max(8, 12 / globalScale);
          const nodeSize = getNodeSize(node.type, node.properties);
          
          // Draw node with enhanced styling
          ctx.font = `${fontSize}px Inter`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          
          // Node fill
          ctx.fillStyle = getNodeColor(node.type);
          ctx.beginPath();
          ctx.arc(node.x!, node.y!, nodeSize, 0, 2 * Math.PI);
          ctx.fill();
          
          // Node border
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = Math.max(1, 2 / globalScale);
          ctx.stroke();
          
          // Text shadow for better readability
          ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
          ctx.shadowBlur = 2;
          ctx.fillStyle = '#ffffff';
          ctx.fillText(label, node.x!, node.y! + nodeSize + 5);
          ctx.shadowBlur = 0;
        }}
        linkCanvasObject={(link: Record<string, unknown>, ctx: CanvasRenderingContext2D) => {
          // Enhanced edge visualization with opacity and thickness
          const opacity = getEdgeOpacity(link);
          const thickness = (link.properties && typeof link.properties === 'object' && 'weight' in link.properties) 
            ? Math.max(1, (link.properties.weight as number) * 3) 
            : 1;
          
          ctx.globalAlpha = opacity;
          ctx.strokeStyle = '#666666';
          ctx.lineWidth = thickness;
          ctx.beginPath();
          ctx.moveTo((link.source as PositionedGraphNode).x!, (link.source as PositionedGraphNode).y!);
          ctx.lineTo((link.target as PositionedGraphNode).x!, (link.target as PositionedGraphNode).y!);
          ctx.stroke();
          ctx.globalAlpha = 1.0;
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
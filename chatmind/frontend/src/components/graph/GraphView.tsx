import React, { useEffect, useRef, useState } from 'react';
import type { GraphNode, GraphEdge } from '../../types';

interface GraphViewProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  width?: number;
  height?: number;
  onNodeClick?: (node: GraphNode) => void;
}

interface NodePosition {
  x: number;
  y: number;
  level: number; // 0 = topics, 1 = chats, 2 = messages
}

export const GraphView: React.FC<GraphViewProps> = ({
  nodes,
  edges,
  width = 800,
  height = 600,
  onNodeClick,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [scale, setScale] = useState(1);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [positions, setPositions] = useState<Map<string, NodePosition>>(new Map());

  // Initialize hierarchical positions
  useEffect(() => {
    if (!canvasRef.current || nodes.length === 0) return;

    const newPositions = new Map<string, NodePosition>();
    const centerX = width / 2;
    const centerY = height / 2;

    // Group nodes by type and level
    const topics = nodes.filter(n => n.type === 'Topic');
    const chats = nodes.filter(n => n.type === 'Chat');
    const messages = nodes.filter(n => n.type === 'Message');

    // Level 0: Topics (always visible)
    topics.forEach((node, index) => {
      const angle = (index / topics.length) * 2 * Math.PI;
      const radius = Math.min(width, height) * 0.3;
      newPositions.set(node.id, {
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
        level: 0
      });
    });

    // Level 1: Chats (visible when zoomed in)
    chats.forEach((node, index) => {
      const angle = (index / chats.length) * 2 * Math.PI;
      const radius = Math.min(width, height) * 0.2;
      newPositions.set(node.id, {
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
        level: 1
      });
    });

    // Level 2: Messages (visible when very zoomed in)
    messages.forEach((node, index) => {
      const angle = (index / messages.length) * 2 * Math.PI;
      const radius = Math.min(width, height) * 0.1;
      newPositions.set(node.id, {
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
        level: 2
      });
    });

    setPositions(newPositions);
  }, [nodes, width, height]);

  // Render function
  useEffect(() => {
    if (!canvasRef.current || nodes.length === 0 || positions.size === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Determine which nodes to show based on zoom level
    const visibleNodes = nodes.filter(node => {
      const pos = positions.get(node.id);
      if (!pos) return false;
      
      if (scale < 0.5) return pos.level === 0; // Only topics
      if (scale < 1.0) return pos.level <= 1;  // Topics and chats
      return true; // All nodes when zoomed in
    });

    // Draw edges (only between visible nodes)
    ctx.strokeStyle = '#4b5563';
    ctx.lineWidth = 1;
    edges.forEach(edge => {
      const source = positions.get(edge.source);
      const target = positions.get(edge.target);
      if (source && target && 
          visibleNodes.some(n => n.id === edge.source) && 
          visibleNodes.some(n => n.id === edge.target)) {
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
      }
    });

    // Draw nodes
    visibleNodes.forEach(node => {
      const pos = positions.get(node.id);
      if (!pos) return;

      const isHovered = hoveredNode === node.id;
      const baseSize = getNodeSize(node.type, pos.level);
      const nodeSize = isHovered ? baseSize * 1.5 : baseSize;
      
      // Node circle
      ctx.fillStyle = getNodeColor(node.type);
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, nodeSize, 0, 2 * Math.PI);
      ctx.fill();
      
      // Node border
      ctx.strokeStyle = isHovered ? '#ffffff' : '#ffffff';
      ctx.lineWidth = isHovered ? 3 : 2;
      ctx.stroke();

      // Node label (only show for hovered or large nodes)
      if (isHovered || baseSize > 8) {
        ctx.fillStyle = '#ffffff';
        ctx.font = '11px Inter';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const label = node.properties.title || String(node.id).substring(0, 8);
        ctx.fillText(label, pos.x, pos.y + nodeSize + 12);
      }
    });

  }, [nodes, edges, positions, hoveredNode, scale, width, height]);

  const getNodeSize = (type: string, level: number) => {
    switch (type) {
      case 'Topic':
        return Math.max(12, Math.min(20, 16 - level * 2));
      case 'Chat':
        return Math.max(8, Math.min(16, 12 - level * 2));
      case 'Message':
        return Math.max(4, Math.min(12, 8 - level * 2));
      default:
        return 8;
    }
  };

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'Chat':
        return '#3b82f6'; // blue
      case 'Topic':
        return '#f59e0b'; // amber
      case 'Message':
        return '#10b981'; // green
      default:
        return '#6b7280'; // gray
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return;
    
    const rect = canvasRef.current.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - offset.x) / scale;
    const mouseY = (e.clientY - rect.top - offset.y) / scale;
    
    // Find closest visible node
    let closestNode: string | null = null;
    let closestDistance = Infinity;
    
    const visibleNodes = nodes.filter(node => {
      const pos = positions.get(node.id);
      if (!pos) return false;
      
      if (scale < 0.5) return pos.level === 0;
      if (scale < 1.0) return pos.level <= 1;
      return true;
    });
    
    for (const node of visibleNodes) {
      const pos = positions.get(node.id);
      if (!pos) continue;
      
      const distance = Math.sqrt((mouseX - pos.x) ** 2 + (mouseY - pos.y) ** 2);
      const nodeSize = getNodeSize(node.type, pos.level);
      if (distance < nodeSize * 2 && distance < closestDistance) {
        closestDistance = distance;
        closestNode = node.id;
      }
    }
    
    setHoveredNode(closestNode);
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    const rect = canvasRef.current?.getBoundingClientRect();
    if (rect) {
      setDragStart({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    }
  };

  const handleMouseMoveDrag = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDragging) return;
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (rect) {
      const newOffset = {
        x: offset.x + (e.clientX - rect.left - dragStart.x),
        y: offset.y + (e.clientY - rect.top - dragStart.y),
      };
      setOffset(newOffset);
      setDragStart({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleClick = () => {
    if (hoveredNode && onNodeClick) {
      const node = nodes.find(n => n.id === hoveredNode);
      if (node) {
        onNodeClick(node);
      }
    }
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const newScale = Math.max(0.2, Math.min(3, scale - e.deltaY * 0.001));
    setScale(newScale);
  };

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={(e) => {
          handleMouseMove(e);
          handleMouseMoveDrag(e);
        }}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onClick={handleClick}
        onWheel={handleWheel}
      />
      
      {/* Graph controls */}
      <div className="absolute top-4 right-4 flex space-x-2">
        <button
          onClick={() => {
            setOffset({ x: 0, y: 0 });
            setScale(1);
          }}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow"
          title="Reset view"
        >
          🔄
        </button>
        <button
          onClick={() => setScale(Math.min(3, scale + 0.2))}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow"
          title="Zoom in"
        >
          ➕
        </button>
        <button
          onClick={() => setScale(Math.max(0.2, scale - 0.2))}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow"
          title="Zoom out"
        >
          ➖
        </button>
      </div>

      {/* Info panel */}
      <div className="absolute bottom-4 left-4 bg-white dark:bg-gray-800 rounded-lg p-3 shadow-md">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          <div>Nodes: {nodes.filter(n => {
            const pos = positions.get(n.id);
            if (!pos) return false;
            if (scale < 0.5) return pos.level === 0;
            if (scale < 1.0) return pos.level <= 1;
            return true;
          }).length}</div>
          <div>Edges: {edges.length}</div>
          <div>Scale: {scale.toFixed(2)}x</div>
          <div>Level: {scale < 0.5 ? 'Topics' : scale < 1.0 ? 'Chats' : 'All'}</div>
        </div>
      </div>
    </div>
  );
}; 
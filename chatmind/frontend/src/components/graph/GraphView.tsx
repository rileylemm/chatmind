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
  vx: number;
  vy: number;
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

  // Initialize force simulation
  useEffect(() => {
    if (!canvasRef.current || nodes.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Initialize positions in a more spread out way
    const newPositions = new Map<string, NodePosition>();
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.4;

    nodes.forEach((node, index) => {
      // Use different starting positions based on node type
      let x, y;
      if (node.type === 'Chat') {
        // Chats in the center
        const angle = (index / nodes.filter(n => n.type === 'Chat').length) * 2 * Math.PI;
        x = centerX + Math.cos(angle) * radius * 0.3;
        y = centerY + Math.sin(angle) * radius * 0.3;
      } else if (node.type === 'Topic') {
        // Topics around the edges
        const angle = (index / nodes.filter(n => n.type === 'Topic').length) * 2 * Math.PI;
        x = centerX + Math.cos(angle) * radius * 0.8;
        y = centerY + Math.sin(angle) * radius * 0.8;
      } else {
        // Messages scattered
        x = centerX + (Math.random() - 0.5) * radius * 0.6;
        y = centerY + (Math.random() - 0.5) * radius * 0.6;
      }

      newPositions.set(node.id, {
        x,
        y,
        vx: 0,
        vy: 0,
      });
    });

    setPositions(newPositions);
  }, [nodes, width, height]);

  // Force simulation
  useEffect(() => {
    if (!canvasRef.current || nodes.length === 0 || positions.size === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    const animate = () => {
      // Clear canvas
      ctx.clearRect(0, 0, width, height);

      // Apply forces
      const newPositions = new Map(positions);
      
      // Repulsion between all nodes
      for (const [id1, pos1] of newPositions) {
        for (const [id2, pos2] of newPositions) {
          if (id1 === id2) continue;
          
          const dx = pos2.x - pos1.x;
          const dy = pos2.y - pos1.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          if (distance > 0 && distance < 100) {
            const force = (100 - distance) / distance * 0.1;
            pos1.vx -= dx * force;
            pos1.vy -= dy * force;
            pos2.vx += dx * force;
            pos2.vy += dy * force;
          }
        }
      }

      // Attraction along edges
      edges.forEach(edge => {
        const source = newPositions.get(edge.source);
        const target = newPositions.get(edge.target);
        if (source && target) {
          const dx = target.x - source.x;
          const dy = target.y - source.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          if (distance > 0) {
            const force = (distance - 50) / distance * 0.05;
            source.vx += dx * force;
            source.vy += dy * force;
            target.vx -= dx * force;
            target.vy -= dy * force;
          }
        }
      });

      // Update positions
      for (const pos of newPositions.values()) {
        pos.x += pos.vx;
        pos.y += pos.vy;
        pos.vx *= 0.95; // Damping
        pos.vy *= 0.95;
        
        // Keep nodes within bounds
        pos.x = Math.max(50, Math.min(width - 50, pos.x));
        pos.y = Math.max(50, Math.min(height - 50, pos.y));
      }

      setPositions(newPositions);

      // Draw edges
      ctx.strokeStyle = '#4b5563';
      ctx.lineWidth = 1;
      edges.forEach(edge => {
        const source = newPositions.get(edge.source);
        const target = newPositions.get(edge.target);
        if (source && target) {
          ctx.beginPath();
          ctx.moveTo(source.x, source.y);
          ctx.lineTo(target.x, target.y);
          ctx.stroke();
        }
      });

      // Draw nodes
      nodes.forEach(node => {
        const pos = newPositions.get(node.id);
        if (!pos) return;

        const size = Math.max(6, Math.min(16, (node.properties.size || 1) * 1.5));
        const isHovered = hoveredNode === node.id;
        const nodeSize = isHovered ? size * 1.5 : size;
        
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
        if (isHovered || size > 10) {
          ctx.fillStyle = '#ffffff';
          ctx.font = '11px Inter';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          const label = node.properties.title || String(node.id).substring(0, 8);
          ctx.fillText(label, pos.x, pos.y + nodeSize + 12);
        }
      });

      animationId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [nodes, edges, positions, hoveredNode, width, height]);

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
    
    // Find closest node
    let closestNode: string | null = null;
    let closestDistance = Infinity;
    
    for (const [nodeId, pos] of positions) {
      const distance = Math.sqrt((mouseX - pos.x) ** 2 + (mouseY - pos.y) ** 2);
      if (distance < 20 && distance < closestDistance) {
        closestDistance = distance;
        closestNode = nodeId;
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
    const newScale = Math.max(0.5, Math.min(2, scale - e.deltaY * 0.001));
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
          onClick={() => setScale(Math.min(2, scale + 0.1))}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow"
          title="Zoom in"
        >
          ➕
        </button>
        <button
          onClick={() => setScale(Math.max(0.5, scale - 0.1))}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow"
          title="Zoom out"
        >
          ➖
        </button>
      </div>

      {/* Info panel */}
      <div className="absolute bottom-4 left-4 bg-white dark:bg-gray-800 rounded-lg p-3 shadow-md">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          <div>Nodes: {nodes.length}</div>
          <div>Edges: {edges.length}</div>
          <div>Scale: {scale.toFixed(2)}x</div>
        </div>
      </div>
    </div>
  );
}; 
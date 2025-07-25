import React, { useEffect, useRef, useState } from 'react';
import type { GraphNode, GraphEdge } from '../../types';

interface GraphViewProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  width?: number;
  height?: number;
}

export const GraphView: React.FC<GraphViewProps> = ({
  nodes,
  edges,
  width = 800,
  height = 600,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [scale, setScale] = useState(1);

  useEffect(() => {
    if (!canvasRef.current || nodes.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Initialize positions
    const newPositions = new Map();
    nodes.forEach((node, index) => {
      const angle = (index / nodes.length) * 2 * Math.PI;
      const radius = Math.min(width, height) * 0.3;
      newPositions.set(node.id, {
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
      });
    });

    // Simple force simulation
    let animationId: number;
    const animate = () => {
      ctx.clearRect(0, 0, width, height);
      
      // Draw edges
      ctx.strokeStyle = '#999';
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

        const size = Math.max(8, Math.min(20, (node.properties.size || 1) * 2));
        
        // Node circle
        ctx.fillStyle = getNodeColor(node.type);
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, size, 0, 2 * Math.PI);
        ctx.fill();
        
        // Node border
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Node label
        ctx.fillStyle = '#374151';
        ctx.font = '12px Inter';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const label = node.properties.title || node.id;
        ctx.fillText(label, pos.x, pos.y + size + 15);
      });

      animationId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [nodes, edges, width, height]);

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'Chat':
        return '#3b82f6'; // blue
      case 'Message':
        return '#10b981'; // green
      case 'Topic':
        return '#f59e0b'; // amber
      case 'Tag':
        return '#8b5cf6'; // purple
      default:
        return '#6b7280'; // gray
    }
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

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
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
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
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
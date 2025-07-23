import React from 'react';
import { Box, CircularProgress } from '@mui/material';
import CytoscapeComponent from 'react-cytoscapejs';
import { GraphData } from '../../types';

interface GraphProps {
  graphData: GraphData | null;
  loading: boolean;
  onNodeClick: (evt: any) => void;
}

export const Graph: React.FC<GraphProps> = ({ graphData, loading, onNodeClick }) => {
  // Convert graph data to Cytoscape format
  const cytoscapeElements = React.useMemo(() => {
    if (!graphData) return [];

    const elements: any[] = [];
    const nodeIds = new Set();

    // Add nodes
    graphData.nodes.forEach(node => {
      nodeIds.add(node.id);
      elements.push({
        data: {
          id: node.id,
          label: node.properties.title || node.properties.name || node.id,
          type: node.type,
          ...node.properties
        }
      });
    });

    // Add edges (only if both source and target nodes exist)
    graphData.edges.forEach(edge => {
      if (nodeIds.has(edge.source) && nodeIds.has(edge.target)) {
        elements.push({
          data: {
            id: `${edge.source}-${edge.target}`,
            source: edge.source,
            target: edge.target,
            type: edge.type
          }
        });
      } else {
        console.warn(`Skipping edge ${edge.source}-${edge.target}: missing nodes`);
      }
    });

    return elements;
  }, [graphData]);

  // Simple circle layout for maximum stability
  const layout = {
    name: 'circle',
    animate: false,
    nodeDimensionsIncludeLabels: true,
    fit: true,
    padding: 50,
    radius: undefined,
    startAngle: 3/2 * Math.PI,
    sweep: undefined,
    clockwise: true,
    sort: undefined
  };

  // Enhanced Cytoscape styles
  const stylesheet = [
    {
      selector: 'node',
      style: {
        'background-color': '#666',
        'label': 'data(label)',
        'text-wrap': 'wrap',
        'text-max-width': '120px',
        'font-size': '11px',
        'text-valign': 'center',
        'text-halign': 'center',
        'width': '25px',
        'height': '25px',
        'border-width': 2,
        'border-color': '#fff',
        'text-outline-width': 1,
        'text-outline-color': '#000',
        'text-background-color': 'rgba(255,255,255,0.8)',
        'text-background-padding': '3px',
        'text-background-opacity': 0.8
      }
    },
    {
      selector: 'node[type = "Topic"]',
      style: {
        'background-color': '#ff6b6b',
        'width': '35px',
        'height': '35px',
        'font-size': '12px',
        'font-weight': 'bold',
        'border-width': 3,
        'border-color': '#ff4757'
      }
    },
    {
      selector: 'node[type = "Chat"]',
      style: {
        'background-color': '#4ecdc4',
        'width': '30px',
        'height': '30px',
        'border-width': 2,
        'border-color': '#26de81'
      }
    },
    {
      selector: 'node[type = "Message"]',
      style: {
        'background-color': '#45b7d1',
        'width': '20px',
        'height': '20px',
        'font-size': '9px',
        'border-width': 1,
        'border-color': '#2ed573'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 2,
        'line-color': '#ddd',
        'target-arrow-color': '#ddd',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'opacity': 0.7
      }
    },
    {
      selector: 'edge[type = "SUMMARIZES"]',
      style: {
        'line-color': '#ff6b6b',
        'target-arrow-color': '#ff6b6b',
        'width': 3,
        'opacity': 0.9
      }
    },
    {
      selector: 'edge[type = "CONTAINS"]',
      style: {
        'line-color': '#4ecdc4',
        'target-arrow-color': '#4ecdc4',
        'width': 2,
        'opacity': 0.8
      }
    },
    {
      selector: 'node:selected',
      style: {
        'border-width': 4,
        'border-color': '#ffd700',
        'background-color': '#ffed4e'
      }
    },
    {
      selector: 'edge:selected',
      style: {
        'line-color': '#ffd700',
        'target-arrow-color': '#ffd700',
        'width': 4
      }
    }
  ];

  return (
    <Box sx={{ 
      flex: 1, 
      position: 'relative',
      mx: 2,
      mb: 2,
      borderRadius: 2,
      overflow: 'hidden',
      bgcolor: 'white',
      boxShadow: 2
    }}>
      {loading && (
        <Box
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
          display="flex"
          alignItems="center"
          justifyContent="center"
          bgcolor="rgba(255,255,255,0.8)"
          zIndex={1}
        >
          <CircularProgress />
        </Box>
      )}
      
      <CytoscapeComponent
        elements={cytoscapeElements}
        layout={layout}
        stylesheet={stylesheet}
        style={{ width: '100%', height: '100%' }}
        cy={(cy: any) => {
          cy.on('tap', 'node', onNodeClick);
          cy.on('layoutstop', () => {
            console.log('Layout completed');
          });
        }}
      />
    </Box>
  );
}; 
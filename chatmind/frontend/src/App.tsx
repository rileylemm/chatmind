import * as React from 'react';
import { useState, useEffect } from 'react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Box, 
  Drawer, 
  List, 
  ListItem, 
  ListItemText,
  ListItemIcon,
  IconButton,
  Paper,
  Chip,
  Divider,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Grid,
  Fab,
  Tooltip,
  Badge,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Avatar,
  Stack,
  Button,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Topic as TopicIcon,
  Chat as ChatIcon,
  Search as SearchIcon,
  Menu as MenuIcon,
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as VisibilityIcon,
  Message as MessageIcon,
  Timeline as TimelineIcon,
  FilterList as FilterListIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import CytoscapeComponent from 'react-cytoscapejs';
import axios from 'axios';
import TagFilter from './components/TagFilter';

// Types
interface Node {
  id: string;
  type: string;
  properties: any;
}

interface Edge {
  source: string;
  target: string;
  type: string;
}

interface GraphData {
  nodes: Node[];
  edges: Edge[];
}

interface Topic {
  id: number;
  name: string;
  size: number;
  top_words: string[];
  sample_titles: string[];
}

interface Chat {
  id: string;
  title: string;
  create_time?: number;
}

interface Message {
  id: string;
  content: string;
  role: string;
  timestamp?: number;
  cluster_id?: number;
}

interface FilterState {
  selectedTags: string[];
  selectedCategory: string | null;
  searchQuery: string;
}

const API_BASE = 'http://localhost:8000';

function App() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [chats, setChats] = useState<Chat[]>([]);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activeFilters, setActiveFilters] = useState<FilterState>({
    selectedTags: [],
    selectedCategory: null,
    searchQuery: ''
  });
  const [selectedTab, setSelectedTab] = useState(0);
  const [graphLoading, setGraphLoading] = useState(false);

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Load graph data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Load graph data
        const graphResponse = await axios.get(`${API_BASE}/graph?limit=50`);
        setGraphData(graphResponse.data);

        // Load topics
        const topicsResponse = await axios.get(`${API_BASE}/topics`);
        setTopics(topicsResponse.data);

        // Load chats
        const chatsResponse = await axios.get(`${API_BASE}/chats?limit=50`);
        setChats(chatsResponse.data);

      } catch (err: any) {
        console.error('Error loading data:', err);
        setError(err.response?.data?.detail || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Load filtered data when filters change
  useEffect(() => {
    const loadFilteredData = async () => {
      if (activeFilters.selectedTags.length > 0 || activeFilters.selectedCategory || activeFilters.searchQuery) {
        try {
          setGraphLoading(true);
          const params = new URLSearchParams();
          if (activeFilters.selectedTags.length > 0) {
            params.append('tags', activeFilters.selectedTags.join(','));
          }
          if (activeFilters.selectedCategory) {
            params.append('category', activeFilters.selectedCategory);
          }
          if (activeFilters.searchQuery) {
            params.append('query', activeFilters.searchQuery);
          }

          const response = await axios.get(`${API_BASE}/graph/filtered?${params.toString()}`);
          setGraphData(response.data);
        } catch (err: any) {
          console.error('Error loading filtered data:', err);
        } finally {
          setGraphLoading(false);
        }
      }
    };

    loadFilteredData();
  }, [activeFilters]);

  const handleFilterChange = (filters: FilterState) => {
    setActiveFilters(filters);
  };

  const handleClearFilters = () => {
    setActiveFilters({
      selectedTags: [],
      selectedCategory: null,
      searchQuery: ''
    });
  };

  // Refresh data
  const handleRefresh = async () => {
    try {
      setLoading(true);
      setError(null);

      const graphResponse = await axios.get(`${API_BASE}/graph?limit=50`);
      setGraphData(graphResponse.data);

      const topicsResponse = await axios.get(`${API_BASE}/topics`);
      setTopics(topicsResponse.data);

      const chatsResponse = await axios.get(`${API_BASE}/chats?limit=50`);
      setChats(chatsResponse.data);

    } catch (err: any) {
      console.error('Error refreshing data:', err);
      setError(err.response?.data?.detail || 'Failed to refresh data');
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = async (evt: any) => {
    const node = evt.target;
    const nodeData = node.data();
    
    try {
      let messagesResponse;
      if (nodeData.type === 'Chat') {
        messagesResponse = await axios.get(`${API_BASE}/chats/${nodeData.id}/messages`);
      } else if (nodeData.type === 'Topic') {
        messagesResponse = await axios.get(`${API_BASE}/topics/${nodeData.id}/messages`);
      } else {
        return;
      }
      
      setMessages(messagesResponse.data);
      setSelectedNode({
        type: nodeData.type,
        id: nodeData.id,
        label: nodeData.label,
        properties: nodeData
      });
    } catch (err) {
      console.error('Error loading messages:', err);
    }
  };

  const handleSearch = async (query: string) => {
    try {
      const response = await axios.get(`${API_BASE}/search?query=${encodeURIComponent(query)}&limit=50`);
      setMessages(response.data);
      setSelectedNode({
        type: 'Search',
        label: `Search: ${query}`,
        query: query
      });
    } catch (err) {
      console.error('Error searching:', err);
    }
  };

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
    radius: undefined, // Let it calculate automatically
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

  if (loading) {
    return (
      <Box 
        display="flex" 
        flexDirection="column"
        justifyContent="center" 
        alignItems="center" 
        height="100vh"
        sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
      >
        <CircularProgress size={60} sx={{ color: 'white', mb: 3 }} />
        <Typography variant="h5" color="white" gutterBottom>
          Loading ChatMind...
        </Typography>
        <Typography variant="body1" color="white" sx={{ opacity: 0.8 }}>
          Connecting to your AI memory graph
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box 
        display="flex" 
        flexDirection="column"
        justifyContent="center" 
        alignItems="center" 
        height="100vh"
        sx={{ background: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%)' }}
      >
        <Alert severity="error" sx={{ mb: 2, maxWidth: 500 }}>
          {error}
        </Alert>
        <Button 
          variant="contained" 
          onClick={handleRefresh}
          startIcon={<RefreshIcon />}
        >
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: '#f5f5f5' }}>
      {/* Enhanced App Bar */}
      <AppBar 
        position="fixed" 
        sx={{ 
          zIndex: (theme) => theme.zIndex.drawer + 1,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setDrawerOpen(!drawerOpen)}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            ChatMind - AI Memory Visualization
          </Typography>
          <Tooltip title="Refresh Data">
            <IconButton color="inherit" onClick={handleRefresh}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      {/* Enhanced Sidebar */}
      <Drawer
        variant={isMobile ? "temporary" : "persistent"}
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        sx={{
          width: 320,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: 320,
            boxSizing: 'border-box',
            marginTop: '64px',
            bgcolor: '#fff',
            borderRight: '1px solid #e0e0e0'
          },
        }}
      >
        <Box sx={{ overflow: 'auto', p: 2 }}>
          {/* Stats Cards */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={6}>
              <Card sx={{ bgcolor: '#e3f2fd' }}>
                <CardContent sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {topics.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Topics
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6}>
              <Card sx={{ bgcolor: '#f3e5f5' }}>
                <CardContent sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="secondary">
                    {chats.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Chats
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Topics Section */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box display="flex" alignItems="center">
                <TopicIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">
                  Topics ({topics.length})
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <List dense>
                {topics.slice(0, 8).map((topic) => (
                  <ListItem 
                    key={topic.id}
                    button
                    onClick={() => {
                      setSelectedNode({ type: 'Topic', topic_id: topic.id, label: topic.name });
                      handleSearch(topic.top_words.join(' '));
                      if (isMobile) setDrawerOpen(false);
                    }}
                    sx={{ 
                      borderRadius: 1, 
                      mb: 0.5,
                      '&:hover': { bgcolor: 'primary.light', color: 'white' }
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <TopicIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={topic.name}
                      secondary={`${topic.size} messages`}
                      primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
                      secondaryTypographyProps={{ variant: 'caption' }}
                    />
                  </ListItem>
                ))}
              </List>
            </AccordionDetails>
          </Accordion>

          {/* Chats Section */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box display="flex" alignItems="center">
                <ChatIcon sx={{ mr: 1, color: 'secondary.main' }} />
                <Typography variant="h6">
                  Recent Chats ({chats.length})
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <List dense>
                {chats.slice(0, 8).map((chat) => (
                  <ListItem 
                    key={chat.id}
                    button
                    onClick={() => {
                      setSelectedNode({ type: 'Chat', chat_id: chat.id, label: chat.title });
                      handleSearch(chat.title);
                      if (isMobile) setDrawerOpen(false);
                    }}
                    sx={{ 
                      borderRadius: 1, 
                      mb: 0.5,
                      '&:hover': { bgcolor: 'secondary.light', color: 'white' }
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <ChatIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={chat.title}
                      secondary={chat.create_time ? new Date(chat.create_time * 1000).toLocaleDateString() : ''}
                      primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
                      secondaryTypographyProps={{ variant: 'caption' }}
                    />
                  </ListItem>
                ))}
              </List>
            </AccordionDetails>
          </Accordion>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box sx={{ 
        flexGrow: 1, 
        display: 'flex', 
        flexDirection: 'column', 
        marginTop: '64px',
        bgcolor: '#fafafa'
      }}>
        {/* Enhanced Filter Section */}
        <Paper 
          elevation={1} 
          sx={{ 
            m: 2, 
            p: 2, 
            borderRadius: 2,
            background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)'
          }}
        >
          <Box display="flex" alignItems="center" mb={2}>
            <FilterListIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              Filter & Search
            </Typography>
            <Button 
              size="small" 
              onClick={handleClearFilters}
              disabled={!activeFilters.selectedTags.length && !activeFilters.selectedCategory && !activeFilters.searchQuery}
            >
              Clear All
            </Button>
          </Box>
          <TagFilter 
            onFilterChange={handleFilterChange}
            onClearFilters={handleClearFilters}
          />
        </Paper>

        {/* Graph Container */}
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
          {graphLoading && (
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
              cy.on('tap', 'node', handleNodeClick);
              // Add layout ready event
              cy.on('layoutstop', () => {
                console.log('Layout completed');
              });
            }}
          />
        </Box>
      </Box>

      {/* Enhanced Messages Panel */}
      {selectedNode && (
        <Paper 
          sx={{ 
            width: isMobile ? '100%' : 450, 
            height: '100vh',
            marginTop: '64px',
            borderRadius: 0,
            boxShadow: 3,
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          {/* Panel Header */}
          <Box 
            sx={{ 
              p: 2, 
              borderBottom: '1px solid #e0e0e0',
              bgcolor: 'primary.main',
              color: 'white'
            }}
          >
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {selectedNode.label}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.8 }}>
                  {messages.length} messages
                </Typography>
              </Box>
              <IconButton 
                onClick={() => setSelectedNode(null)}
                sx={{ color: 'white' }}
              >
                <CloseIcon />
              </IconButton>
            </Box>
          </Box>

          {/* Messages Content */}
          <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
            {messages.length === 0 ? (
              <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" height="100%">
                <MessageIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No messages found
                </Typography>
                <Typography variant="body2" color="text.secondary" textAlign="center">
                  Try selecting a different node or adjusting your search
                </Typography>
              </Box>
            ) : (
              <Stack spacing={2}>
                {messages.map((message) => (
                  <Card 
                    key={message.id} 
                    sx={{ 
                      bgcolor: message.role === 'user' ? '#e3f2fd' : '#f3e5f5',
                      border: '1px solid',
                      borderColor: message.role === 'user' ? 'primary.light' : 'secondary.light'
                    }}
                  >
                    <CardContent sx={{ p: 2 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Chip 
                          label={message.role} 
                          size="small"
                          color={message.role === 'user' ? 'primary' : 'secondary'}
                          icon={message.role === 'user' ? <VisibilityIcon /> : <InfoIcon />}
                        />
                        {message.timestamp && (
                          <Typography variant="caption" color="text.secondary">
                            {new Date(message.timestamp * 1000).toLocaleString()}
                          </Typography>
                        )}
                      </Box>
                      <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                        {message.content}
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            )}
          </Box>
        </Paper>
      )}

      {/* Floating Action Button for Mobile */}
      {isMobile && (
        <Fab
          color="primary"
          aria-label="menu"
          onClick={() => setDrawerOpen(true)}
          sx={{
            position: 'fixed',
            bottom: 16,
            left: 16,
            zIndex: 1000
          }}
        >
          <MenuIcon />
        </Fab>
      )}
    </Box>
  );
}

export default App;

import React, { useState, useEffect } from 'react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Box, 
  IconButton,
  Paper,
  Button,
  CircularProgress,
  Alert,
  Fab,
  Tooltip,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Menu as MenuIcon,
  Refresh as RefreshIcon,
  FilterList as FilterListIcon
} from '@mui/icons-material';
import TagFilter from './components/TagFilter';
import { Graph } from './components/graph/Graph';
import { Sidebar } from './components/sidebar/Sidebar';
import { Messages } from './components/messages/Messages';
import { useGraphData } from './hooks/useGraphData';
import { useMessages } from './hooks/useMessages';
import { FilterState } from './types';

function App() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activeFilters, setActiveFilters] = useState<FilterState>({
    selectedTags: [],
    selectedCategory: null,
    searchQuery: ''
  });

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Custom hooks
  const {
    graphData,
    topics,
    chats,
    loading,
    error,
    graphLoading,
    loadFilteredData,
    refreshData
  } = useGraphData();

  const {
    selectedNode,
    messages,
    handleNodeClick,
    handleTopicClick,
    handleChatClick,
    clearSelection
  } = useMessages();

  // Load filtered data when filters change
  useEffect(() => {
    loadFilteredData(activeFilters);
  }, [activeFilters, loadFilteredData]);

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
          onClick={refreshData}
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
            <IconButton color="inherit" onClick={refreshData}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Sidebar
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        topics={topics}
        chats={chats}
        onTopicClick={handleTopicClick}
        onChatClick={handleChatClick}
      />

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

        {/* Graph */}
        <Graph
          graphData={graphData}
          loading={graphLoading}
          onNodeClick={handleNodeClick}
        />
      </Box>

      {/* Messages Panel - only show when a node is selected */}
      {selectedNode && (
        <Box sx={{ position: 'fixed', right: 0, top: '64px', bottom: 0, zIndex: 1200 }}>
          <Messages
            selectedNode={selectedNode}
            messages={messages}
            onClose={clearSelection}
          />
        </Box>
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
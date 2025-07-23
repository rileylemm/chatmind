import React from 'react';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Typography,
  Card,
  CardContent,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Topic as TopicIcon,
  Chat as ChatIcon,
  ExpandMore as ExpandMoreIcon
} from '@mui/icons-material';
import { Topic, Chat } from '../../types';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  topics: Topic[];
  chats: Chat[];
  onTopicClick: (topic: Topic) => void;
  onChatClick: (chat: Chat) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  open,
  onClose,
  topics,
  chats,
  onTopicClick,
  onChatClick
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  return (
    <Drawer
      variant={isMobile ? "temporary" : "persistent"}
      anchor="left"
      open={open}
      onClose={onClose}
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
                    onTopicClick(topic);
                    if (isMobile) onClose();
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
                    onChatClick(chat);
                    if (isMobile) onClose();
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
  );
}; 
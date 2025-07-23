import React from 'react';
import {
  Paper,
  Box,
  Typography,
  IconButton,
  Card,
  CardContent,
  Chip,
  Stack,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Close as CloseIcon,
  Message as MessageIcon,
  Visibility as VisibilityIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { Message, SelectedNode } from '../../types';

interface MessagesProps {
  selectedNode: SelectedNode | null;
  messages: Message[];
  onClose: () => void;
}

export const Messages: React.FC<MessagesProps> = ({ selectedNode, messages, onClose }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  if (!selectedNode) return null;

  return (
    <Paper 
      sx={{ 
        width: isMobile ? '100%' : 450, 
        height: '100%',
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
            onClick={onClose}
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
  );
}; 
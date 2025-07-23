import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AttachMoney,
  Api,
  Timeline,
  Download
} from '@mui/icons-material';

interface CostStatistics {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  success_rate: number;
  total_cost_usd: number;
  total_input_tokens: number;
  total_output_tokens: number;
  model_statistics: Record<string, any>;
  operation_statistics: Record<string, any>;
  date_range: {
    start_date: string | null;
    end_date: string | null;
  };
}

interface RecentCall {
  id: number;
  timestamp: number;
  model: string;
  operation: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  success: boolean;
  error_message?: string;
}

interface DailyCost {
  date: string;
  daily_cost: number;
  daily_calls: number;
  daily_input_tokens: number;
  daily_output_tokens: number;
}

const CostTracker: React.FC = () => {
  const [statistics, setStatistics] = useState<CostStatistics | null>(null);
  const [recentCalls, setRecentCalls] = useState<RecentCall[]>([]);
  const [dailyCosts, setDailyCosts] = useState<DailyCost[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Filter states
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [selectedOperation, setSelectedOperation] = useState<string>('');

  const API_BASE = 'http://localhost:8000';

  const fetchCostStatistics = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (selectedOperation) params.append('operation', selectedOperation);
      
      const response = await fetch(`${API_BASE}/costs/statistics?${params}`);
      if (!response.ok) throw new Error('Failed to fetch cost statistics');
      
      const data = await response.json();
      setStatistics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const fetchRecentCalls = async () => {
    try {
      const response = await fetch(`${API_BASE}/costs/recent?limit=20`);
      if (!response.ok) throw new Error('Failed to fetch recent calls');
      
      const data = await response.json();
      setRecentCalls(data);
    } catch (err) {
      console.error('Failed to fetch recent calls:', err);
    }
  };

  const fetchDailyCosts = async () => {
    try {
      const response = await fetch(`${API_BASE}/costs/daily?days=30`);
      if (!response.ok) throw new Error('Failed to fetch daily costs');
      
      const data = await response.json();
      setDailyCosts(data);
    } catch (err) {
      console.error('Failed to fetch daily costs:', err);
    }
  };

  const exportCostData = async () => {
    try {
      const response = await fetch(`${API_BASE}/costs/export`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to export cost data');
      
      const data = await response.json();
      alert(`Cost data exported: ${data.message}`);
    } catch (err) {
      alert('Failed to export cost data');
    }
  };

  useEffect(() => {
    fetchCostStatistics();
    fetchRecentCalls();
    fetchDailyCosts();
  }, [startDate, endDate, selectedOperation]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  const formatTokens = (tokens: number) => {
    return new Intl.NumberFormat('en-US').format(tokens);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <AttachMoney sx={{ mr: 1, verticalAlign: 'middle' }} />
        Cost Tracker
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Filters
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={3}>
              <TextField
                fullWidth
                label="Start Date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <TextField
                fullWidth
                label="End Date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>Operation</InputLabel>
                <Select
                  value={selectedOperation}
                  label="Operation"
                  onChange={(e) => setSelectedOperation(e.target.value)}
                >
                  <MenuItem value="">All Operations</MenuItem>
                  <MenuItem value="chunking">Chunking</MenuItem>
                  <MenuItem value="tagging">Tagging</MenuItem>
                  <MenuItem value="embedding">Embedding</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Button
                variant="contained"
                onClick={exportCostData}
                startIcon={<Download />}
                fullWidth
              >
                Export Data
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Statistics Overview */}
      {statistics && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <AttachMoney color="primary" sx={{ mr: 1 }} />
                  <Box>
                    <Typography variant="h6">
                      {formatCurrency(statistics.total_cost_usd)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Cost
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <Api color="primary" sx={{ mr: 1 }} />
                  <Box>
                    <Typography variant="h6">
                      {statistics.total_calls}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Calls
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <TrendingUp color="success" sx={{ mr: 1 }} />
                  <Box>
                    <Typography variant="h6">
                      {(statistics.success_rate * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Success Rate
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <Timeline color="primary" sx={{ mr: 1 }} />
                  <Box>
                    <Typography variant="h6">
                      {formatTokens(statistics.total_input_tokens + statistics.total_output_tokens)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Tokens
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Model Statistics */}
      {statistics?.model_statistics && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Cost by Model
            </Typography>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Model</TableCell>
                    <TableCell align="right">Calls</TableCell>
                    <TableCell align="right">Cost</TableCell>
                    <TableCell align="right">Input Tokens</TableCell>
                    <TableCell align="right">Output Tokens</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(statistics.model_statistics).map(([model, stats]) => (
                    <TableRow key={model}>
                      <TableCell>
                        <Chip label={model} size="small" />
                      </TableCell>
                      <TableCell align="right">{stats.calls}</TableCell>
                      <TableCell align="right">{formatCurrency(stats.cost)}</TableCell>
                      <TableCell align="right">{formatTokens(stats.input_tokens)}</TableCell>
                      <TableCell align="right">{formatTokens(stats.output_tokens)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Recent Calls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent API Calls
          </Typography>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Time</TableCell>
                  <TableCell>Model</TableCell>
                  <TableCell>Operation</TableCell>
                  <TableCell align="right">Cost</TableCell>
                  <TableCell align="right">Tokens</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recentCalls.map((call) => (
                  <TableRow key={call.id}>
                    <TableCell>{formatDate(call.timestamp)}</TableCell>
                    <TableCell>
                      <Chip label={call.model} size="small" />
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={call.operation} 
                        size="small" 
                        color="primary" 
                      />
                    </TableCell>
                    <TableCell align="right">
                      {formatCurrency(call.cost_usd)}
                    </TableCell>
                    <TableCell align="right">
                      {formatTokens(call.input_tokens + call.output_tokens)}
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={call.success ? 'Success' : 'Failed'} 
                        size="small" 
                        color={call.success ? 'success' : 'error'} 
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Daily Costs Chart */}
      {dailyCosts.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Daily Costs (Last 30 Days)
            </Typography>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell align="right">Cost</TableCell>
                    <TableCell align="right">Calls</TableCell>
                    <TableCell align="right">Tokens</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dailyCosts.map((daily) => (
                    <TableRow key={daily.date}>
                      <TableCell>{daily.date}</TableCell>
                      <TableCell align="right">
                        {formatCurrency(daily.daily_cost)}
                      </TableCell>
                      <TableCell align="right">{daily.daily_calls}</TableCell>
                      <TableCell align="right">
                        {formatTokens(daily.daily_input_tokens + daily.daily_output_tokens)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default CostTracker; 
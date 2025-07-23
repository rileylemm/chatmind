import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Autocomplete,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Alert,
  CircularProgress,
  Grid
} from '@mui/material';
import {
  FilterList,
  Clear,
  Search,
  Tag
} from '@mui/icons-material';

interface TagFilterProps {
  onFilterChange: (filters: FilterState) => void;
  onClearFilters: () => void;
}

interface FilterState {
  selectedTags: string[];
  selectedCategory: string | null;
  searchQuery: string;
}

interface AvailableTags {
  tags: string[];
  categories: string[];
}

const TagFilter: React.FC<TagFilterProps> = ({ onFilterChange, onClearFilters }) => {
  const [availableTags, setAvailableTags] = useState<AvailableTags>({ tags: [], categories: [] });
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = 'http://localhost:8000';

  // Load available tags and categories
  useEffect(() => {
    const loadTags = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`${API_BASE}/tags`);
        if (!response.ok) throw new Error('Failed to fetch tags');
        
        const data = await response.json();
        setAvailableTags(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    loadTags();
  }, []);

  // Apply filters when they change
  useEffect(() => {
    const filters: FilterState = {
      selectedTags,
      selectedCategory,
      searchQuery
    };
    onFilterChange(filters);
  }, [selectedTags, selectedCategory, searchQuery, onFilterChange]);

  const handleTagChange = (event: any, newValue: string[]) => {
    setSelectedTags(newValue);
  };

  const handleCategoryChange = (event: any) => {
    setSelectedCategory(event.target.value);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
  };

  const handleClearFilters = () => {
    setSelectedTags([]);
    setSelectedCategory(null);
    setSearchQuery('');
    onClearFilters();
  };

  const hasActiveFilters = selectedTags.length > 0 || selectedCategory || searchQuery;

  if (loading) {
    return (
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="100px">
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          <FilterList sx={{ mr: 1 }} />
          <Typography variant="h6">
            Filter by Tags & Categories
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={2}>
          {/* Tags Filter */}
          <Grid item xs={12} md={6}>
            <Autocomplete
              multiple
              options={availableTags.tags}
              value={selectedTags}
              onChange={handleTagChange}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Filter by Tags"
                  placeholder="Select tags..."
                  variant="outlined"
                  size="small"
                />
              )}
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip
                    {...getTagProps({ index })}
                    key={option}
                    label={option}
                    color="primary"
                    size="small"
                    icon={<Tag />}
                  />
                ))
              }
              renderOption={(props, option) => (
                <Box component="li" {...props}>
                  <Tag sx={{ mr: 1, fontSize: 'small' }} />
                  {option}
                </Box>
              )}
            />
          </Grid>

          {/* Category Filter */}
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Category</InputLabel>
              <Select
                value={selectedCategory || ''}
                label="Category"
                onChange={handleCategoryChange}
              >
                <MenuItem value="">
                  <em>All Categories</em>
                </MenuItem>
                {availableTags.categories.map((category) => (
                  <MenuItem key={category} value={category}>
                    {category}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Search Query */}
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              size="small"
              label="Search Content"
              value={searchQuery}
              onChange={handleSearchChange}
              placeholder="Search messages..."
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, fontSize: 'small' }} />
              }}
            />
          </Grid>
        </Grid>

        {/* Active Filters Display */}
        {hasActiveFilters && (
          <Box mt={2}>
            <Divider sx={{ mb: 1 }} />
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Active Filters:
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {selectedTags.map((tag) => (
                <Chip
                  key={tag}
                  label={`Tag: ${tag}`}
                  size="small"
                  color="primary"
                  onDelete={() => setSelectedTags(selectedTags.filter(t => t !== tag))}
                />
              ))}
              {selectedCategory && (
                <Chip
                  label={`Category: ${selectedCategory}`}
                  size="small"
                  color="secondary"
                  onDelete={() => setSelectedCategory(null)}
                />
              )}
              {searchQuery && (
                <Chip
                  label={`Search: "${searchQuery}"`}
                  size="small"
                  color="info"
                  onDelete={() => setSearchQuery('')}
                />
              )}
            </Box>
          </Box>
        )}

        {/* Clear Filters Button */}
        {hasActiveFilters && (
          <Box mt={2}>
            <Button
              variant="outlined"
              startIcon={<Clear />}
              onClick={handleClearFilters}
              size="small"
            >
              Clear All Filters
            </Button>
          </Box>
        )}

        {/* Statistics */}
        <Box mt={2}>
          <Typography variant="body2" color="text.secondary">
            Available: {availableTags.tags.length} tags, {availableTags.categories.length} categories
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default TagFilter; 
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { FilterState, TagFilter } from '../types';

interface FilterStore extends FilterState {
  // Tag filter state
  tagFilter: TagFilter;
  
  // Actions
  setTags: (tags: string[]) => void;
  setDateRange: (start: Date | null, end: Date | null) => void;
  setRole: (role: 'all' | 'user' | 'assistant') => void;
  setSearchQuery: (query: string) => void;
  
  // Tag filter actions
  setSelectedTags: (tags: string[]) => void;
  setSelectedCategory: (category: string | null) => void;
  setTagSearchQuery: (query: string) => void;
  
  // Reset
  resetFilters: () => void;
}

const initialState: FilterState = {
  tags: [],
  dateRange: { start: null, end: null },
  role: 'all',
  searchQuery: '',
};

const initialTagFilter: TagFilter = {
  selectedTags: [],
  selectedCategory: null,
  searchQuery: '',
};

export const useFilterStore = create<FilterStore>()(
  persist(
    (set) => ({
      ...initialState,
      tagFilter: initialTagFilter,

      setTags: (tags) => set({ tags }),
      setDateRange: (start, end) => set({ dateRange: { start, end } }),
      setRole: (role) => set({ role }),
      setSearchQuery: (query) => set({ searchQuery: query }),
      
      setSelectedTags: (selectedTags) => set((state) => ({
        tagFilter: { ...state.tagFilter, selectedTags }
      })),
      
      setSelectedCategory: (selectedCategory) => set((state) => ({
        tagFilter: { ...state.tagFilter, selectedCategory }
      })),
      
      setTagSearchQuery: (searchQuery) => set((state) => ({
        tagFilter: { ...state.tagFilter, searchQuery }
      })),
      
      resetFilters: () => set({
        ...initialState,
        tagFilter: initialTagFilter,
      }),
    }),
    {
      name: 'chatmind-filters',
      partialize: (state) => ({
        tags: state.tags,
        role: state.role,
        tagFilter: state.tagFilter,
      }),
    }
  )
); 
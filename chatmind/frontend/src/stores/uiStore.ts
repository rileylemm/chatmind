import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UIState, GraphNode, Theme } from '../types';

interface UIStore extends UIState {
  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
  setSelectedNode: (node: GraphNode | null) => void;
  toggleCommandPalette: () => void;
  setCommandPaletteOpen: (open: boolean) => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      // Initial state
      sidebarOpen: true,
      theme: { mode: 'light' },
      selectedNode: null,
      commandPaletteOpen: false,

      // Actions
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      
      toggleTheme: () => set((state) => ({
        theme: { mode: state.theme.mode === 'light' ? 'dark' : 'light' }
      })),
      
      setTheme: (theme) => set({ theme }),
      
      setSelectedNode: (node) => set({ selectedNode: node }),
      
      toggleCommandPalette: () => set((state) => ({ 
        commandPaletteOpen: !state.commandPaletteOpen 
      })),
      
      setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
    }),
    {
      name: 'chatmind-ui',
      partialize: (state) => ({
        theme: state.theme,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
); 
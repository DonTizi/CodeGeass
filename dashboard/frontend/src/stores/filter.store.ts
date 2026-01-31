import { create } from 'zustand';
import type { TaskFilterCriteria } from '@/types';

interface FilterState {
  // Filter values
  search: string;
  tags: string[];
  status: 'success' | 'failed' | 'never_run' | undefined;
  model: 'sonnet' | 'haiku' | 'opus' | undefined;
  enabled: boolean | undefined;

  // Actions
  setSearch: (search: string) => void;
  setTags: (tags: string[]) => void;
  addTag: (tag: string) => void;
  removeTag: (tag: string) => void;
  setStatus: (status: 'success' | 'failed' | 'never_run' | undefined) => void;
  setModel: (model: 'sonnet' | 'haiku' | 'opus' | undefined) => void;
  setEnabled: (enabled: boolean | undefined) => void;
  clearFilters: () => void;
  hasActiveFilters: () => boolean;
  getFilterCriteria: () => TaskFilterCriteria;
}

export const useFilterStore = create<FilterState>((set, get) => ({
  // Initial state
  search: '',
  tags: [],
  status: undefined,
  model: undefined,
  enabled: undefined,

  // Actions
  setSearch: (search: string) => set({ search }),

  setTags: (tags: string[]) => set({ tags }),

  addTag: (tag: string) =>
    set((state) => ({
      tags: state.tags.includes(tag) ? state.tags : [...state.tags, tag],
    })),

  removeTag: (tag: string) =>
    set((state) => ({
      tags: state.tags.filter((t) => t !== tag),
    })),

  setStatus: (status) => set({ status }),

  setModel: (model) => set({ model }),

  setEnabled: (enabled) => set({ enabled }),

  clearFilters: () =>
    set({
      search: '',
      tags: [],
      status: undefined,
      model: undefined,
      enabled: undefined,
    }),

  hasActiveFilters: () => {
    const state = get();
    return (
      state.search !== '' ||
      state.tags.length > 0 ||
      state.status !== undefined ||
      state.model !== undefined ||
      state.enabled !== undefined
    );
  },

  getFilterCriteria: (): TaskFilterCriteria => {
    const state = get();
    const criteria: TaskFilterCriteria = {};

    if (state.search) criteria.search = state.search;
    if (state.tags.length > 0) criteria.tags = state.tags;
    if (state.status) criteria.status = state.status;
    if (state.model) criteria.model = state.model;
    if (state.enabled !== undefined) criteria.enabled = state.enabled;

    return criteria;
  },
}));

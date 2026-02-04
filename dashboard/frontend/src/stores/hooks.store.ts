import { create } from 'zustand';
import type { Hook, HookSummary, HookCreate, HookPreview, HookValidation } from '@/types';
import { api } from '@/lib/api';

interface HooksState {
  hooks: HookSummary[];
  selectedHook: Hook | null;
  templates: string[];
  loading: boolean;
  error: string | null;

  fetchHooks: () => Promise<void>;
  fetchHook: (tag: string) => Promise<void>;
  fetchTemplates: () => Promise<void>;
  createHook: (data: HookCreate) => Promise<void>;
  deleteHook: (tag: string) => Promise<void>;
  initTemplates: (overwrite?: boolean) => Promise<string[]>;
  previewHooks: (tags: string[]) => Promise<HookPreview>;
  validateHook: (tag: string) => Promise<HookValidation>;
  selectHook: (hook: Hook | null) => void;
  clearError: () => void;
}

export const useHooksStore = create<HooksState>((set) => ({
  hooks: [],
  selectedHook: null,
  templates: [],
  loading: false,
  error: null,

  fetchHooks: async () => {
    set({ loading: true, error: null });
    try {
      const hooks = await api.hooks.list();
      set({ hooks, loading: false });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to fetch hooks', loading: false });
    }
  },

  fetchHook: async (tag: string) => {
    set({ loading: true, error: null });
    try {
      const hook = await api.hooks.get(tag);
      set({ selectedHook: hook, loading: false });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to fetch hook', loading: false });
    }
  },

  fetchTemplates: async () => {
    try {
      const templates = await api.hooks.listTemplates();
      set({ templates });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to fetch templates' });
    }
  },

  createHook: async (data: HookCreate) => {
    set({ loading: true, error: null });
    try {
      await api.hooks.create(data);
      // Refresh the list
      const hooks = await api.hooks.list();
      set({ hooks, loading: false });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to create hook', loading: false });
      throw e;
    }
  },

  deleteHook: async (tag: string) => {
    set({ loading: true, error: null });
    try {
      await api.hooks.delete(tag);
      // Refresh the list
      const hooks = await api.hooks.list();
      set({ hooks, selectedHook: null, loading: false });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to delete hook', loading: false });
      throw e;
    }
  },

  initTemplates: async (overwrite = false) => {
    set({ loading: true, error: null });
    try {
      const initialized = await api.hooks.initTemplates(overwrite);
      // Refresh the list
      const hooks = await api.hooks.list();
      set({ hooks, loading: false });
      return initialized;
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to init templates', loading: false });
      throw e;
    }
  },

  previewHooks: async (tags: string[]) => {
    try {
      return await api.hooks.preview(tags);
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to preview hooks' });
      throw e;
    }
  },

  validateHook: async (tag: string) => {
    try {
      return await api.hooks.validate(tag);
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to validate hook' });
      throw e;
    }
  },

  selectHook: (hook: Hook | null) => {
    set({ selectedHook: hook });
  },

  clearError: () => {
    set({ error: null });
  },
}));

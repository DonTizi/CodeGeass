import { create } from 'zustand';
import type { SchedulerStatus, UpcomingRun, ExecutionResult } from '@/types';
import { api } from '@/lib/api';

interface SchedulerState {
  status: SchedulerStatus | null;
  upcoming: UpcomingRun[];
  loading: boolean;
  error: string | null;

  fetchStatus: () => Promise<void>;
  fetchUpcoming: (hours?: number) => Promise<void>;
  runDue: (windowSeconds?: number, dryRun?: boolean) => Promise<ExecutionResult[]>;
}

export const useSchedulerStore = create<SchedulerState>((set) => ({
  status: null,
  upcoming: [],
  loading: false,
  error: null,

  fetchStatus: async () => {
    try {
      const status = await api.scheduler.getStatus();
      set({ status });
    } catch (e) {
      console.error('Failed to fetch scheduler status:', e);
    }
  },

  fetchUpcoming: async (hours = 24) => {
    set({ loading: true, error: null });
    try {
      const upcoming = await api.scheduler.getUpcoming(hours);
      set({ upcoming, loading: false });
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to fetch upcoming runs',
        loading: false,
      });
    }
  },

  runDue: async (windowSeconds = 60, dryRun = false) => {
    set({ loading: true, error: null });
    try {
      const results = await api.scheduler.runDue(windowSeconds, dryRun);
      set({ loading: false });
      return results;
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to run due tasks',
        loading: false,
      });
      throw e;
    }
  },
}));

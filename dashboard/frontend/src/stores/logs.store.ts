import { create } from 'zustand';
import type { ExecutionResult, ExecutionStatus, LogStats } from '@/types';
import { api } from '@/lib/api';

interface LogsState {
  logs: ExecutionResult[];
  stats: LogStats | null;
  loading: boolean;
  error: string | null;

  // Filter state
  statusFilter: ExecutionStatus | null;
  taskFilter: string | null;

  fetchLogs: () => Promise<void>;
  fetchTaskLogs: (taskId: string, limit?: number) => Promise<ExecutionResult[]>;
  fetchStats: () => Promise<void>;
  clearTaskLogs: (taskId: string) => Promise<void>;
  setStatusFilter: (status: ExecutionStatus | null) => void;
  setTaskFilter: (taskId: string | null) => void;
}

export const useLogsStore = create<LogsState>((set, get) => ({
  logs: [],
  stats: null,
  loading: false,
  error: null,
  statusFilter: null,
  taskFilter: null,

  fetchLogs: async () => {
    set({ loading: true, error: null });
    try {
      const { statusFilter, taskFilter } = get();
      const logs = await api.logs.list({
        status: statusFilter ?? undefined,
        task_id: taskFilter ?? undefined,
        limit: 100,
      });
      set({ logs, loading: false });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to fetch logs', loading: false });
    }
  },

  fetchTaskLogs: async (taskId: string, limit = 10) => {
    try {
      return await api.logs.getForTask(taskId, limit);
    } catch (e) {
      console.error('Failed to fetch task logs:', e);
      return [];
    }
  },

  fetchStats: async () => {
    try {
      const stats = await api.logs.getStats();
      set({ stats });
    } catch (e) {
      console.error('Failed to fetch stats:', e);
    }
  },

  clearTaskLogs: async (taskId: string) => {
    set({ loading: true, error: null });
    try {
      await api.logs.clearForTask(taskId);
      set((state) => ({
        logs: state.logs.filter((log) => log.task_id !== taskId),
        loading: false,
      }));
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to clear logs', loading: false });
      throw e;
    }
  },

  setStatusFilter: (status: ExecutionStatus | null) => {
    set({ statusFilter: status });
  },

  setTaskFilter: (taskId: string | null) => {
    set({ taskFilter: taskId });
  },
}));

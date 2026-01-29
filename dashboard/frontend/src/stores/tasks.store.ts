import { create } from 'zustand';
import type { Task, TaskCreate, TaskUpdate, TaskStats, ExecutionResult } from '@/types';
import { api } from '@/lib/api';

interface TasksState {
  tasks: Task[];
  selectedTask: Task | null;
  taskStats: Record<string, TaskStats>;
  loading: boolean;
  error: string | null;

  fetchTasks: () => Promise<void>;
  fetchTask: (taskId: string) => Promise<void>;
  fetchTaskStats: (taskId: string) => Promise<void>;
  createTask: (data: TaskCreate) => Promise<Task>;
  updateTask: (taskId: string, data: TaskUpdate) => Promise<Task>;
  deleteTask: (taskId: string) => Promise<void>;
  enableTask: (taskId: string) => Promise<void>;
  disableTask: (taskId: string) => Promise<void>;
  runTask: (taskId: string, dryRun?: boolean) => Promise<ExecutionResult>;
  selectTask: (task: Task | null) => void;
}

export const useTasksStore = create<TasksState>((set) => ({
  tasks: [],
  selectedTask: null,
  taskStats: {},
  loading: false,
  error: null,

  fetchTasks: async () => {
    set({ loading: true, error: null });
    try {
      const tasks = await api.tasks.list();
      set({ tasks, loading: false });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to fetch tasks', loading: false });
    }
  },

  fetchTask: async (taskId: string) => {
    set({ loading: true, error: null });
    try {
      const task = await api.tasks.get(taskId);
      set({ selectedTask: task, loading: false });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to fetch task', loading: false });
    }
  },

  fetchTaskStats: async (taskId: string) => {
    try {
      const stats = await api.tasks.getStats(taskId);
      set((state) => ({
        taskStats: { ...state.taskStats, [taskId]: stats },
      }));
    } catch (e) {
      console.error('Failed to fetch task stats:', e);
    }
  },

  createTask: async (data: TaskCreate) => {
    set({ loading: true, error: null });
    try {
      const task = await api.tasks.create(data);
      set((state) => ({
        tasks: [...state.tasks, task],
        loading: false,
      }));
      return task;
    } catch (e) {
      const error = e instanceof Error ? e.message : 'Failed to create task';
      set({ error, loading: false });
      throw e;
    }
  },

  updateTask: async (taskId: string, data: TaskUpdate) => {
    set({ loading: true, error: null });
    try {
      const task = await api.tasks.update(taskId, data);
      set((state) => ({
        tasks: state.tasks.map((t) => (t.id === taskId ? task : t)),
        selectedTask: state.selectedTask?.id === taskId ? task : state.selectedTask,
        loading: false,
      }));
      return task;
    } catch (e) {
      const error = e instanceof Error ? e.message : 'Failed to update task';
      set({ error, loading: false });
      throw e;
    }
  },

  deleteTask: async (taskId: string) => {
    set({ loading: true, error: null });
    try {
      await api.tasks.delete(taskId);
      set((state) => ({
        tasks: state.tasks.filter((t) => t.id !== taskId),
        selectedTask: state.selectedTask?.id === taskId ? null : state.selectedTask,
        loading: false,
      }));
    } catch (e) {
      const error = e instanceof Error ? e.message : 'Failed to delete task';
      set({ error, loading: false });
      throw e;
    }
  },

  enableTask: async (taskId: string) => {
    try {
      await api.tasks.enable(taskId);
      set((state) => ({
        tasks: state.tasks.map((t) =>
          t.id === taskId ? { ...t, enabled: true } : t
        ),
        selectedTask:
          state.selectedTask?.id === taskId
            ? { ...state.selectedTask, enabled: true }
            : state.selectedTask,
      }));
    } catch (e) {
      throw e;
    }
  },

  disableTask: async (taskId: string) => {
    try {
      await api.tasks.disable(taskId);
      set((state) => ({
        tasks: state.tasks.map((t) =>
          t.id === taskId ? { ...t, enabled: false } : t
        ),
        selectedTask:
          state.selectedTask?.id === taskId
            ? { ...state.selectedTask, enabled: false }
            : state.selectedTask,
      }));
    } catch (e) {
      throw e;
    }
  },

  runTask: async (taskId: string, dryRun = false) => {
    try {
      const result = await api.tasks.run(taskId, dryRun);
      // Refresh the task to get updated last_run
      const task = await api.tasks.get(taskId);
      set((state) => ({
        tasks: state.tasks.map((t) => (t.id === taskId ? task : t)),
        selectedTask: state.selectedTask?.id === taskId ? task : state.selectedTask,
      }));
      return result;
    } catch (e) {
      throw e;
    }
  },

  selectTask: (task: Task | null) => {
    set({ selectedTask: task });
  },
}));

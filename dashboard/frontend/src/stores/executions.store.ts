import { create } from 'zustand';
import type { ActiveExecution, ExecutionEvent } from '@/types/execution';
import { api } from '@/lib/api';

// Extended execution with completion info
interface ExtendedExecution extends ActiveExecution {
  completed?: boolean;
  completedAt?: string;
  exitCode?: number;
  error?: string;
  success?: boolean;
  approval_id?: string | null;
}

interface ExecutionsState {
  // Active executions keyed by execution_id
  activeExecutions: Record<string, ExtendedExecution>;
  // WebSocket connection status
  wsConnected: boolean;
  // Error state
  error: string | null;

  // Actions
  fetchActiveExecutions: () => Promise<void>;
  handleEvent: (event: ExecutionEvent) => void;
  setWsConnected: (connected: boolean) => void;
  clearError: () => void;
  getByTaskId: (taskId: string) => ExtendedExecution | undefined;
  dismissExecution: (executionId: string) => void;
}

export const useExecutionsStore = create<ExecutionsState>((set, get) => ({
  activeExecutions: {},
  wsConnected: false,
  error: null,

  fetchActiveExecutions: async () => {
    try {
      const executions = await api.executions.list();
      const mapped: Record<string, ActiveExecution> = {};
      for (const ex of executions) {
        mapped[ex.execution_id] = ex;
      }
      set({ activeExecutions: mapped, error: null });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to fetch executions' });
    }
  },

  handleEvent: (event: ExecutionEvent) => {
    const { type, execution_id, task_id, task_name, timestamp, data } = event;

    set((state) => {
      const executions = { ...state.activeExecutions };

      switch (type) {
        case 'execution.started': {
          // Remove any completed executions for the same task
          // This ensures new execution (e.g., approval after plan) takes precedence
          for (const [id, ex] of Object.entries(executions)) {
            if (ex.task_id === task_id && ex.completed) {
              delete executions[id];
            }
          }
          // Add new execution
          executions[execution_id] = {
            execution_id,
            task_id,
            task_name,
            session_id: (data.session_id as string) || null,
            started_at: timestamp,
            status: 'starting',
            output_lines: [],
            current_phase: 'initializing',
          };
          break;
        }

        case 'execution.output': {
          // Append output line
          const exec = executions[execution_id];
          if (exec) {
            const line = data.line as string;
            const output_lines = [...exec.output_lines, line];
            // Keep only last 1000 lines to match backend buffer
            if (output_lines.length > 1000) {
              output_lines.splice(0, output_lines.length - 1000);
            }
            executions[execution_id] = { ...exec, output_lines };
          }
          break;
        }

        case 'execution.progress': {
          // Update phase
          const exec = executions[execution_id];
          if (exec) {
            executions[execution_id] = {
              ...exec,
              status: 'running',
              current_phase: (data.phase as string) || exec.current_phase,
            };
          }
          break;
        }

        case 'execution.completed': {
          // Mark as completed but keep visible
          const exec = executions[execution_id];
          if (exec) {
            executions[execution_id] = {
              ...exec,
              status: 'finishing',
              completed: true,
              completedAt: timestamp,
              success: true,
              exitCode: (data.exit_code as number) || 0,
            };
          }
          break;
        }

        case 'execution.failed': {
          // Mark as failed but keep visible
          const exec = executions[execution_id];
          if (exec) {
            executions[execution_id] = {
              ...exec,
              status: 'finishing',
              completed: true,
              completedAt: timestamp,
              success: false,
              error: (data.error as string) || 'Unknown error',
              exitCode: (data.exit_code as number) || 1,
            };
          }
          break;
        }

        case 'execution.waiting_approval': {
          // Plan mode task waiting for user approval
          const exec = executions[execution_id];
          if (exec) {
            executions[execution_id] = {
              ...exec,
              status: 'waiting_approval',
              current_phase: 'waiting for approval',
              approval_id: (data.approval_id as string) || null,
            };
          }
          break;
        }

        case 'execution.stopped': {
          // Execution was manually stopped
          const exec = executions[execution_id];
          if (exec) {
            executions[execution_id] = {
              ...exec,
              status: 'finishing',
              current_phase: 'stopped',
              completed: true,
              completedAt: timestamp,
              success: false,
              error: (data.reason as string) || 'Stopped by user',
            };
          }
          break;
        }
      }

      return { activeExecutions: executions };
    });
  },

  setWsConnected: (connected: boolean) => {
    set({ wsConnected: connected });
  },

  clearError: () => {
    set({ error: null });
  },

  getByTaskId: (taskId: string) => {
    const { activeExecutions } = get();
    const executions = Object.values(activeExecutions).filter((ex) => ex.task_id === taskId);

    if (executions.length === 0) return undefined;

    // Prefer running executions over completed ones
    const running = executions.find((ex) => !ex.completed);
    if (running) return running;

    // If all are completed, return the most recent one
    return executions.sort((a, b) =>
      new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
    )[0];
  },

  dismissExecution: (executionId: string) => {
    set((state) => {
      const executions = { ...state.activeExecutions };
      delete executions[executionId];
      return { activeExecutions: executions };
    });
  },
}));

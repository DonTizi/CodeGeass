export type ExecutionStatus = 'success' | 'failure' | 'timeout' | 'skipped' | 'running';

export interface ExecutionResult {
  task_id: string;
  task_name: string | null;
  session_id: string | null;
  status: ExecutionStatus;
  output: string;
  error: string | null;
  exit_code: number | null;
  started_at: string;
  finished_at: string | null;
  duration_seconds: number | null;
}

export interface LogFilter {
  status?: ExecutionStatus;
  task_id?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

export interface LogStats {
  total_executions: number;
  successful: number;
  failed: number;
  timeout: number;
  success_rate: number;
  avg_duration_seconds: number;
  last_execution: string | null;
  by_task: Record<string, {
    name: string;
    total: number;
    success: number;
    failure: number;
    success_rate: number;
  }>;
}

export type TaskStatus = 'success' | 'failure' | 'timeout' | 'skipped' | 'running';

export interface TaskNotificationConfig {
  channels: string[];
  events: string[];
  include_output: boolean;
}

export interface Task {
  id: string;
  name: string;
  schedule: string;
  working_dir: string;
  skill: string | null;
  prompt: string | null;
  allowed_tools: string[];
  model: 'haiku' | 'sonnet' | 'opus';
  autonomous: boolean;
  max_turns: number | null;
  timeout: number;
  enabled: boolean;
  variables: Record<string, unknown>;
  notifications: TaskNotificationConfig | null;
  last_run: string | null;
  last_status: TaskStatus | null;
  next_run: string | null;
  schedule_description: string | null;
}

export interface TaskSummary {
  id: string;
  name: string;
  schedule: string;
  skill: string | null;
  enabled: boolean;
  last_run: string | null;
  last_status: TaskStatus | null;
  next_run: string | null;
}

export interface TaskCreate {
  name: string;
  schedule: string;
  working_dir: string;
  skill?: string | null;
  prompt?: string | null;
  allowed_tools?: string[];
  model?: 'haiku' | 'sonnet' | 'opus';
  autonomous?: boolean;
  max_turns?: number | null;
  timeout?: number;
  enabled?: boolean;
  variables?: Record<string, unknown>;
  notifications?: TaskNotificationConfig | null;
}

export interface TaskUpdate {
  name?: string;
  schedule?: string;
  working_dir?: string;
  skill?: string | null;
  prompt?: string | null;
  allowed_tools?: string[];
  model?: 'haiku' | 'sonnet' | 'opus';
  autonomous?: boolean;
  max_turns?: number | null;
  timeout?: number;
  enabled?: boolean;
  variables?: Record<string, unknown>;
  notifications?: TaskNotificationConfig | null;
}

export interface TaskStats {
  task_id: string;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  timeout_runs: number;
  success_rate: number;
  avg_duration_seconds: number;
  last_run: string | null;
  last_status: TaskStatus | null;
}

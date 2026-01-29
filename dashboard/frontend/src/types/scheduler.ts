export interface SchedulerStatus {
  running: boolean;
  check_interval: number;
  max_concurrent: number;
  total_tasks: number;
  enabled_tasks: number;
  due_tasks: number;
  last_check: string | null;
  next_check: string | null;
}

export interface UpcomingRun {
  task_id: string;
  task_name: string;
  schedule: string;
  next_run: string;
  skill: string | null;
  enabled: boolean;
}

export interface Project {
  id: string;
  name: string;
  path: string;
  description: string;
  default_model: 'haiku' | 'sonnet' | 'opus';
  default_timeout: number;
  default_autonomous: boolean;
  git_remote: string | null;
  enabled: boolean;
  use_shared_skills: boolean;
  created_at: string | null;
  task_count: number;
  skill_count: number;
  is_default: boolean;
  exists: boolean;
  is_initialized: boolean;
}

export interface ProjectSummary {
  id: string;
  name: string;
  path: string;
  enabled: boolean;
  is_default: boolean;
  task_count: number;
  skill_count: number;
}

export interface ProjectCreate {
  path: string;
  name?: string | null;
  description?: string;
  default_model?: 'haiku' | 'sonnet' | 'opus';
  default_timeout?: number;
  default_autonomous?: boolean;
  use_shared_skills?: boolean;
}

export interface ProjectUpdate {
  name?: string | null;
  description?: string | null;
  default_model?: 'haiku' | 'sonnet' | 'opus' | null;
  default_timeout?: number | null;
  default_autonomous?: boolean | null;
  use_shared_skills?: boolean | null;
  enabled?: boolean | null;
}

import type { TaskStatus } from './task';

/**
 * Minimal task interface for display purposes.
 * Both Task and TaskWithProject conform to this interface.
 */
export interface TaskBase {
  id: string;
  name: string;
  schedule: string;
  working_dir: string;
  skill: string | null;
  prompt: string | null;
  model: string;
  autonomous: boolean;
  timeout: number;
  enabled: boolean;
  last_run: string | null;
  last_status: TaskStatus | string | null;
  next_run: string | null;
  schedule_description: string | null;
}

export interface TaskWithProject extends TaskBase {
  // Project fields
  project_id: string | null;
  project_name: string | null;
}

export interface SkillWithSource {
  name: string;
  description: string;
  source: 'project' | 'shared';
  path: string;
  allowed_tools: string[];
  context: string;
  agent: string | null;
}

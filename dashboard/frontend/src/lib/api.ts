/**
 * API client for CodeGeass Dashboard
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

/**
 * Build query string from params object
 */
function buildQuery(params: Record<string, unknown>): string {
  const filtered = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null
  );
  if (filtered.length === 0) return '';
  return '?' + new URLSearchParams(
    filtered.map(([k, v]) => [k, String(v)])
  ).toString();
}

// Types imported from @/types
import type {
  Task,
  TaskCreate,
  TaskUpdate,
  TaskStats,
  ExecutionResult,
  ExecutionStatus,
  LogStats,
  Skill,
  SkillSummary,
  SchedulerStatus,
  UpcomingRun,
  Channel,
  ChannelCreate,
  ChannelUpdate,
  ProviderInfo,
  TestResult,
  Project,
  ProjectCreate,
  ProjectUpdate,
  TaskWithProject,
  SkillWithSource,
  ActiveExecution,
  Provider,
} from '@/types';

/**
 * Tasks API
 */
const tasks = {
  list: () => fetchApi<Task[]>('/api/tasks'),

  get: (taskId: string) => fetchApi<Task>(`/api/tasks/${taskId}`),

  create: (data: TaskCreate) =>
    fetchApi<Task>('/api/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (taskId: string, data: TaskUpdate) =>
    fetchApi<Task>(`/api/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (taskId: string) =>
    fetchApi<void>(`/api/tasks/${taskId}`, { method: 'DELETE' }),

  enable: (taskId: string) =>
    fetchApi<void>(`/api/tasks/${taskId}/enable`, { method: 'POST' }),

  disable: (taskId: string) =>
    fetchApi<void>(`/api/tasks/${taskId}/disable`, { method: 'POST' }),

  run: (taskId: string, dryRun = false) =>
    fetchApi<ExecutionResult>(
      `/api/tasks/${taskId}/run${buildQuery({ dry_run: dryRun })}`
      , { method: 'POST' }
    ),

  stop: (taskId: string) =>
    fetchApi<{ status: string; message: string; execution_id: string }>(
      `/api/tasks/${taskId}/stop`,
      { method: 'POST' }
    ),

  getStats: (taskId: string) =>
    fetchApi<TaskStats>(`/api/tasks/${taskId}/stats`),
};

/**
 * Logs API
 */
const logs = {
  list: (params: {
    status?: ExecutionStatus;
    task_id?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  } = {}) => fetchApi<ExecutionResult[]>(`/api/logs${buildQuery(params)}`),

  getForTask: (taskId: string, limit = 10) =>
    fetchApi<ExecutionResult[]>(`/api/logs/task/${taskId}${buildQuery({ limit })}`),

  getLatest: (taskId: string) =>
    fetchApi<ExecutionResult>(`/api/logs/task/${taskId}/latest`),

  getStats: () => fetchApi<LogStats>('/api/logs/stats'),

  clearForTask: (taskId: string) =>
    fetchApi<void>(`/api/logs/task/${taskId}`, { method: 'DELETE' }),
};

/**
 * Skills API
 */
const skills = {
  list: () => fetchApi<SkillSummary[]>('/api/skills'),

  get: (name: string) => fetchApi<Skill>(`/api/skills/${name}`),

  reload: () =>
    fetchApi<SkillSummary[]>('/api/skills/reload', { method: 'POST' }),

  preview: (name: string, args = '') =>
    fetchApi<{ name: string; arguments: string; content: string }>(
      `/api/skills/${name}/preview${buildQuery({ arguments: args })}`
    ),
};

/**
 * Scheduler API
 */
const scheduler = {
  getStatus: () => fetchApi<SchedulerStatus>('/api/scheduler/status'),

  getUpcoming: (hours = 24) =>
    fetchApi<UpcomingRun[]>(`/api/scheduler/upcoming${buildQuery({ hours })}`),

  runDue: (windowSeconds = 60, dryRun = false) =>
    fetchApi<ExecutionResult[]>(
      `/api/scheduler/run-due${buildQuery({ window_seconds: windowSeconds, dry_run: dryRun })}`,
      { method: 'POST' }
    ),

  getDue: (windowSeconds = 60) =>
    fetchApi<Task[]>(`/api/scheduler/due${buildQuery({ window_seconds: windowSeconds })}`),
};

/**
 * Notifications API
 */
const notifications = {
  listChannels: (enabledOnly = false) =>
    fetchApi<Channel[]>(
      `/api/notifications/channels${buildQuery({ enabled_only: enabledOnly })}`
    ),

  getChannel: (channelId: string) =>
    fetchApi<Channel>(`/api/notifications/channels/${channelId}`),

  createChannel: (data: ChannelCreate) =>
    fetchApi<Channel>('/api/notifications/channels', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateChannel: (channelId: string, data: ChannelUpdate) =>
    fetchApi<Channel>(`/api/notifications/channels/${channelId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteChannel: (channelId: string, deleteCredentials = true) =>
    fetchApi<void>(
      `/api/notifications/channels/${channelId}${buildQuery({ delete_credentials: deleteCredentials })}`,
      { method: 'DELETE' }
    ),

  enableChannel: (channelId: string) =>
    fetchApi<void>(`/api/notifications/channels/${channelId}/enable`, {
      method: 'POST',
    }),

  disableChannel: (channelId: string) =>
    fetchApi<void>(`/api/notifications/channels/${channelId}/disable`, {
      method: 'POST',
    }),

  testChannel: (channelId: string) =>
    fetchApi<TestResult>(`/api/notifications/channels/${channelId}/test`, {
      method: 'POST',
    }),

  sendTestMessage: (channelId: string, message = 'Test notification from CodeGeass!') =>
    fetchApi<void>(
      `/api/notifications/channels/${channelId}/send-test${buildQuery({ message })}`,
      { method: 'POST' }
    ),

  listProviders: () => fetchApi<ProviderInfo[]>('/api/notifications/providers'),

  getProvider: (name: string) =>
    fetchApi<ProviderInfo>(`/api/notifications/providers/${name}`),
};

/**
 * Projects API
 */
const projects = {
  list: (enabledOnly = false) =>
    fetchApi<Project[]>(`/api/projects${buildQuery({ enabled_only: enabledOnly })}`),

  get: (projectId: string) => fetchApi<Project>(`/api/projects/${projectId}`),

  add: (data: ProjectCreate) =>
    fetchApi<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (projectId: string, data: ProjectUpdate) =>
    fetchApi<Project>(`/api/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  remove: (projectId: string) =>
    fetchApi<void>(`/api/projects/${projectId}`, { method: 'DELETE' }),

  setDefault: (projectId: string) =>
    fetchApi<void>(`/api/projects/${projectId}/set-default`, { method: 'POST' }),

  enable: (projectId: string) =>
    fetchApi<void>(`/api/projects/${projectId}/enable`, { method: 'POST' }),

  disable: (projectId: string) =>
    fetchApi<void>(`/api/projects/${projectId}/disable`, { method: 'POST' }),

  getTasks: (projectId: string, enabledOnly = false) =>
    fetchApi<TaskWithProject[]>(
      `/api/projects/${projectId}/tasks${buildQuery({ enabled_only: enabledOnly })}`
    ),

  getAllTasks: (enabledOnly = false, projectEnabledOnly = true) =>
    fetchApi<TaskWithProject[]>(
      `/api/projects/tasks/all${buildQuery({
        enabled_only: enabledOnly,
        project_enabled_only: projectEnabledOnly,
      })}`
    ),

  getSkills: (projectId: string) =>
    fetchApi<SkillWithSource[]>(`/api/projects/${projectId}/skills`),

  getDefault: () => fetchApi<Project | null>('/api/projects/default'),
};

/**
 * Executions API (real-time monitoring)
 */
const executions = {
  list: () => fetchApi<ActiveExecution[]>('/api/executions'),

  get: (executionId: string) =>
    fetchApi<ActiveExecution | null>(`/api/executions/${executionId}`),

  getByTask: (taskId: string) =>
    fetchApi<ActiveExecution | null>(`/api/executions/task/${taskId}`),

  /**
   * Create WebSocket connection for real-time execution events
   */
  createWebSocket: (taskId?: string): WebSocket => {
    const endpoint = taskId
      ? `/api/executions/ws/${taskId}`
      : '/api/executions/ws';
    // Use current host with ws/wss protocol when API_BASE_URL is relative
    if (!API_BASE_URL) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      return new WebSocket(`${protocol}//${window.location.host}${endpoint}`);
    }
    const wsBase = API_BASE_URL.replace('http', 'ws');
    return new WebSocket(`${wsBase}${endpoint}`);
  },
};

/**
 * Filesystem API
 */
export interface FolderPickerResult {
  path: string | null;
  cancelled: boolean;
  error: string | null;
}

const filesystem = {
  pickFolder: () => fetchApi<FolderPickerResult>('/api/fs/pick-folder', { method: 'POST' }),
};

/**
 * Code Execution Providers API
 */
const providers = {
  list: () => fetchApi<Provider[]>('/api/providers'),

  get: (name: string) => fetchApi<Provider>(`/api/providers/${name}`),

  listAvailable: () =>
    fetchApi<{ name: string; display_name: string; is_available: boolean; supports_plan_mode: boolean }[]>(
      '/api/providers/available'
    ),
};

/**
 * CRON validation API
 */
const cron = {
  validate: (expression: string) =>
    fetchApi<{
      valid: boolean;
      error?: string;
      description?: string;
      next_runs?: string[];
    }>('/api/cron/validate', {
      method: 'POST',
      body: JSON.stringify({ expression }),
    }),
};

/**
 * Health check API
 */
const health = {
  check: () => fetchApi<{ status: string; timestamp: string }>('/health'),
};

/**
 * Unified API client
 */
export const api = {
  tasks,
  logs,
  skills,
  scheduler,
  notifications,
  projects,
  providers,
  executions,
  filesystem,
  cron,
  health,
};

export default api;

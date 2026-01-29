export type NotificationEvent =
  | 'task_start'
  | 'task_complete'
  | 'task_success'
  | 'task_failure'
  | 'daily_summary';

export interface Channel {
  id: string;
  name: string;
  provider: string;
  credential_key: string;
  config: Record<string, unknown>;
  enabled: boolean;
  created_at: string | null;
}

export interface ChannelCreate {
  name: string;
  provider: string;
  credentials: Record<string, string>;
  config?: Record<string, unknown>;
}

export interface ChannelUpdate {
  name?: string;
  config?: Record<string, unknown>;
  enabled?: boolean;
}

export interface CredentialField {
  name: string;
  description: string;
  sensitive?: boolean;
}

export interface ConfigField {
  name: string;
  description: string;
  default?: unknown;
  sensitive?: boolean;
}

export interface ProviderInfo {
  name: string;
  display_name: string;
  description: string;
  required_credentials: CredentialField[];
  required_config: ConfigField[];
  optional_config: ConfigField[];
}

export interface NotificationConfig {
  channels: string[];
  events: NotificationEvent[];
  include_output: boolean;
  mention_on_failure: boolean;
}

export interface TestResult {
  success: boolean;
  message: string;
}

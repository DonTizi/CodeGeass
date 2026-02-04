/**
 * Hook types for Claude Code hooks management
 */

export interface HookHandler {
  type: 'command' | 'prompt' | 'agent';
  command?: string;
  prompt?: string;
  timeout?: number;
  async?: boolean;
}

export interface HookMatcher {
  matcher?: string;
  hooks: HookHandler[];
}

export type HookEvent =
  | 'PreToolUse'
  | 'PostToolUse'
  | 'PostToolUseFailure'
  | 'Stop'
  | 'SessionStart'
  | 'SessionEnd'
  | 'Notification'
  | 'SubagentStart'
  | 'SubagentStop'
  | 'UserPromptSubmit'
  | 'PermissionRequest'
  | 'PreCompact';

export interface HookSummary {
  tag: string;
  description: string;
  location: 'project' | 'global';
  events: HookEvent[];
}

export interface Hook {
  tag: string;
  description: string;
  location: 'project' | 'global';
  hooks: Record<HookEvent, HookMatcher[]>;
}

export interface HookCreate {
  tag: string;
  description?: string;
  hooks?: Record<string, HookMatcher[]>;
  global_scope?: boolean;
}

export interface HookUpdate {
  description?: string;
  hooks?: Record<string, HookMatcher[]>;
}

export interface HookPreview {
  tags: string[];
  settings_json: string;
  events: HookEvent[];
}

export interface HookValidation {
  tag: string;
  valid: boolean;
  errors: string[];
}

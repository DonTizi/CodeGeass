/**
 * Types for plan approval system
 */

export type ApprovalStatus =
  | 'pending'
  | 'approved'
  | 'executing'
  | 'completed'
  | 'cancelled'
  | 'expired'
  | 'failed';

export interface MessageRef {
  message_id: number | string;
  chat_id: string;
  provider: string;
}

export interface FeedbackEntry {
  feedback: string;
  timestamp: string;
  plan_response: string;
}

export interface Approval {
  id: string;
  task_id: string;
  task_name: string;
  session_id: string;
  plan_text: string;
  working_dir: string;
  status: ApprovalStatus;
  iteration: number;
  max_iterations: number;
  timeout_seconds: number;
  created_at: string;
  expires_at: string;
  channel_messages: MessageRef[];
  feedback_history: FeedbackEntry[];
  final_output: string;
  error: string | null;
}

export interface ApprovalSummary {
  id: string;
  task_id: string;
  task_name: string;
  status: ApprovalStatus;
  iteration: number;
  max_iterations: number;
  created_at: string;
  expires_at: string;
  is_expired: boolean;
}

export interface ApprovalActionResult {
  success: boolean;
  message: string;
  approval: Approval | null;
}

export interface ApprovalStats {
  total: number;
  pending: number;
  approved: number;
  cancelled: number;
  expired: number;
  failed: number;
  completed: number;
}

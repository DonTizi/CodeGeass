import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, Clock, X, CheckCircle, XCircle, PauseCircle, ExternalLink } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import type { ActiveExecution } from '@/types/execution';
import { useExecutionsStore } from '@/stores';
import { ClaudeTerminal } from './ClaudeTerminal';
import type { ParsedLine } from './ClaudeTerminal';

// Extended execution type with completion info
interface ExtendedExecution extends ActiveExecution {
  completed?: boolean;
  completedAt?: string;
  exitCode?: number;
  error?: string;
  success?: boolean;
  approval_id?: string | null;
}

// Internal parsed line with type information
interface InternalParsedLine {
  type: 'text' | 'tool_use' | 'tool_result' | 'thinking' | 'raw';
  content: string;
  toolName?: string;
}

// Parse a stream-json line into a readable format
// Supports both Claude Code (stream-json) and Codex (JSONL) formats
function parseStreamLine(line: string): InternalParsedLine | null {
  try {
    const data = JSON.parse(line);

    // Skip system/init messages - these are metadata, not user-visible content
    if (data.type === 'system') {
      return null;
    }

    // ===== Codex JSONL Format =====
    // Skip thread/turn metadata
    if (data.type === 'thread.started' || data.type === 'turn.started' || data.type === 'turn.completed') {
      return null;
    }

    // Codex item.completed - main response format
    if (data.type === 'item.completed' && data.item) {
      const item = data.item;
      // Extract text from agent_message (skip reasoning/thinking)
      if (item.type === 'agent_message' && item.text) {
        return { type: 'text', content: item.text };
      }
      // Skip reasoning items
      return null;
    }

    // ===== Claude Code stream-json Format =====
    // Skip message_start, message_stop, message_delta, content_block_start/stop metadata
    if (data.type === 'stream_event') {
      const event = data.event;

      // Skip metadata events
      if (event?.type === 'message_start' ||
          event?.type === 'message_stop' ||
          event?.type === 'message_delta' ||
          event?.type === 'content_block_stop') {
        return null;
      }

      // Skip content_block_start for text (empty text block)
      if (event?.type === 'content_block_start' && event.content_block?.type === 'text') {
        return null;
      }

      // Text delta - accumulate text content
      if (event?.type === 'content_block_delta' && event.delta?.type === 'text_delta') {
        return { type: 'text', content: event.delta.text };
      }

      // Tool use start
      if (event?.type === 'content_block_start' && event.content_block?.type === 'tool_use') {
        return {
          type: 'tool_use',
          content: `Using tool: ${event.content_block.name}`,
          toolName: event.content_block.name,
        };
      }

      // Tool input delta - skip these (partial JSON fragments)
      if (event?.type === 'content_block_delta' && event.delta?.type === 'input_json_delta') {
        return null;
      }

      // Thinking delta
      if (event?.type === 'content_block_delta' && event.delta?.type === 'thinking_delta') {
        return { type: 'thinking', content: event.delta.thinking };
      }

      // Skip other stream events
      return null;
    }

    // Handle assistant message with full text content
    if (data.type === 'assistant' && data.message?.content) {
      const textContent = data.message.content
        .filter((block: { type: string }) => block.type === 'text')
        .map((block: { text: string }) => block.text)
        .join('\n');
      if (textContent) {
        return { type: 'text', content: textContent };
      }
      return null;
    }

    // Handle direct tool_use type
    if (data.type === 'tool_use') {
      return {
        type: 'tool_use',
        content: `Tool: ${data.name}`,
        toolName: data.name,
      };
    }

    // Handle result type - show only success/failure
    if (data.type === 'result') {
      return null; // Skip result metadata
    }

    // Skip any other JSON - don't show raw JSON to user
    return null;
  } catch {
    // Not JSON - this is plain text output, show it
    const trimmed = line.trim();
    if (trimmed) {
      return { type: 'text', content: line };
    }
    return null;
  }
}

interface ExecutionMonitorProps {
  execution: ExtendedExecution;
  className?: string;
  compact?: boolean;
}

function formatDuration(startedAt: string, endedAt?: string): string {
  const start = new Date(startedAt);
  const end = endedAt ? new Date(endedAt) : new Date();
  const seconds = Math.floor((end.getTime() - start.getTime()) / 1000);

  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

// Link to approval page for plan mode
function ApprovalLink({ approvalId }: { approvalId: string }) {
  return (
    <Link to={`/approvals/${approvalId}`}>
      <Button size="sm" variant="outline" className="text-orange-600 border-orange-500/50 hover:bg-orange-500/10">
        <ExternalLink className="h-4 w-4 mr-1" />
        View Approval
      </Button>
    </Link>
  );
}

export function ExecutionMonitor({
  execution,
  className,
  compact = false,
}: ExecutionMonitorProps) {
  const [duration, setDuration] = useState(
    formatDuration(execution.started_at, execution.completedAt)
  );
  const dismissExecution = useExecutionsStore((state) => state.dismissExecution);

  const isCompleted = execution.completed;
  const isSuccess = execution.success;
  const isWaitingApproval = execution.status === 'waiting_approval';
  const isLive = !isCompleted && !isWaitingApproval;

  // Parse and format output lines for ClaudeTerminal
  const formattedOutput = useMemo((): ParsedLine[] => {
    const lines: ParsedLine[] = [];
    let currentTextBuffer = '';

    for (const line of execution.output_lines) {
      const parsed = parseStreamLine(line);

      // Skip null results (filtered out metadata)
      if (!parsed) {
        continue;
      }

      if (parsed.type === 'text') {
        // Accumulate text content
        currentTextBuffer += parsed.content;
      } else {
        // Flush text buffer if we have accumulated text
        if (currentTextBuffer) {
          lines.push({ type: 'text', content: currentTextBuffer });
          currentTextBuffer = '';
        }
        // Add the non-text line
        if (parsed.type === 'tool_use') {
          lines.push({ type: 'tool', content: parsed.content, toolName: parsed.toolName });
        } else if (parsed.type === 'thinking') {
          lines.push({ type: 'thinking', content: parsed.content });
        }
      }
    }

    // Flush remaining text buffer
    if (currentTextBuffer) {
      lines.push({ type: 'text', content: currentTextBuffer });
    }

    return lines;
  }, [execution.output_lines]);

  // Update duration every second while running
  useEffect(() => {
    if (isCompleted) {
      setDuration(formatDuration(execution.started_at, execution.completedAt));
      return;
    }
    const interval = setInterval(() => {
      setDuration(formatDuration(execution.started_at));
    }, 1000);
    return () => clearInterval(interval);
  }, [execution.started_at, execution.completedAt, isCompleted]);

  const handleDismiss = () => {
    dismissExecution(execution.execution_id);
  };

  // Determine border and icon colors based on state
  const borderColor = isWaitingApproval
    ? 'border-orange-500/30'
    : isCompleted
      ? isSuccess
        ? 'border-green-500/30'
        : 'border-red-500/30'
      : 'border-blue-500/30';

  const StatusIcon = isWaitingApproval
    ? PauseCircle
    : isCompleted
      ? isSuccess
        ? CheckCircle
        : XCircle
      : Activity;

  const iconColor = isWaitingApproval
    ? 'text-orange-500 animate-pulse'
    : isCompleted
      ? isSuccess
        ? 'text-green-500'
        : 'text-red-500'
      : 'text-blue-500 animate-pulse';

  const statusText = isWaitingApproval
    ? 'Waiting for Approval'
    : isCompleted
      ? isSuccess
        ? 'Completed'
        : 'Failed'
      : execution.status === 'starting'
        ? 'Starting'
        : 'Running';

  return (
    <Card className={cn(borderColor, className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <StatusIcon className={cn('h-4 w-4', iconColor)} />
            {statusText}: {execution.task_name}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {duration}
            </Badge>
            <Badge
              variant="secondary"
              className={cn(
                !isCompleted && !isWaitingApproval && execution.status === 'starting' && 'bg-yellow-500/20 text-yellow-600',
                !isCompleted && !isWaitingApproval && execution.status === 'running' && 'bg-blue-500/20 text-blue-600',
                isWaitingApproval && 'bg-orange-500/20 text-orange-600',
                isCompleted && isSuccess && 'bg-green-500/20 text-green-600',
                isCompleted && !isSuccess && 'bg-red-500/20 text-red-600'
              )}
            >
              {isWaitingApproval ? 'needs approval' : isCompleted ? (isSuccess ? 'success' : 'failed') : execution.status}
            </Badge>
            {(isCompleted || isWaitingApproval) && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={handleDismiss}
                title="Dismiss"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
        {(!isCompleted || isWaitingApproval) && (
          <div className="mt-2">
            {isWaitingApproval && execution.approval_id ? (
              <ApprovalLink approvalId={execution.approval_id} />
            ) : isWaitingApproval ? (
              <span className="text-sm text-orange-500">Waiting for approval...</span>
            ) : (
              <p className="text-sm text-muted-foreground">
                Phase: <span className="font-mono">{execution.current_phase}</span>
              </p>
            )}
          </div>
        )}
        {isCompleted && execution.error && (
          <p className="text-sm text-red-500 mt-1">
            Error: {execution.error}
          </p>
        )}
      </CardHeader>
      <CardContent className="pt-2">
        <ClaudeTerminal
          lines={formattedOutput}
          isLive={isLive}
          title={execution.task_name}
          maxHeight={compact ? 'h-48' : 'h-96'}
        />
      </CardContent>
    </Card>
  );
}

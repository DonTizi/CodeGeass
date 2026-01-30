import { Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';
import type { ActiveExecution } from '@/types/execution';

interface ActiveExecutionBadgeProps {
  execution: ActiveExecution;
  className?: string;
  showDuration?: boolean;
}

function formatDuration(startedAt: string): string {
  const start = new Date(startedAt);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - start.getTime()) / 1000);

  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

export function ActiveExecutionBadge({
  execution,
  className,
  showDuration = true,
}: ActiveExecutionBadgeProps) {
  const statusLabel = {
    starting: 'Starting',
    running: 'Running',
    finishing: 'Finishing',
    waiting_approval: 'Needs Approval',
    stopped: 'Stopped',
  }[execution.status];

  const isWaitingApproval = execution.status === 'waiting_approval';

  return (
    <Badge
      variant="default"
      className={cn(
        isWaitingApproval
          ? 'bg-orange-500/20 text-orange-600 border-orange-500/30'
          : 'bg-blue-500/20 text-blue-600 border-blue-500/30',
        'flex items-center gap-1.5 animate-pulse',
        className
      )}
    >
      <Loader2 className="h-3 w-3 animate-spin" />
      <span>{statusLabel}</span>
      {showDuration && (
        <span className="text-xs opacity-75">
          ({formatDuration(execution.started_at)})
        </span>
      )}
    </Badge>
  );
}

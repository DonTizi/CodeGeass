import { Link } from 'react-router-dom';
import { Play, MoreVertical, Power, PowerOff, Trash2, Clock, Wand2 } from 'lucide-react';
import type { Task } from '@/types';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Switch } from '@/components/ui/Switch';
import { cn, formatRelativeTime, getStatusBgColor, getStatusIcon } from '@/lib/utils';
import { useTasksStore, useExecutionsStore } from '@/stores';
import { toast } from '@/components/ui/Toaster';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';
import { ActiveExecutionBadge } from '@/components/executions';

interface TaskCardProps {
  task: Task;
  onDelete?: () => void;
}

export function TaskCard({ task, onDelete }: TaskCardProps) {
  const { enableTask, disableTask, runTask } = useTasksStore();
  const activeExecution = useExecutionsStore((state) => state.getByTaskId(task.id));
  const isRunning = !!activeExecution;

  const handleToggleEnabled = async () => {
    try {
      if (task.enabled) {
        await disableTask(task.id);
        toast({ title: 'Task disabled', variant: 'default' });
      } else {
        await enableTask(task.id);
        toast({ title: 'Task enabled', variant: 'success' });
      }
    } catch (e) {
      toast({ title: 'Failed to toggle task', variant: 'destructive' });
    }
  };

  const handleRun = async () => {
    try {
      const result = await runTask(task.id);
      if (result.status === 'success') {
        toast({ title: 'Task completed successfully', variant: 'success' });
      } else {
        toast({ title: `Task ${result.status}`, variant: 'destructive' });
      }
    } catch (e) {
      toast({
        title: 'Failed to run task',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <Link
              to={`/tasks/${task.id}`}
              className="text-lg font-medium hover:text-primary transition-colors"
            >
              {task.name}
            </Link>
            {isRunning ? (
              <ActiveExecutionBadge execution={activeExecution} showDuration />
            ) : (
              <Badge variant={task.enabled ? 'success' : 'secondary'}>
                {task.enabled ? 'Enabled' : 'Disabled'}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Switch checked={task.enabled} onCheckedChange={handleToggleEnabled} />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleRun}>
                  <Play className="h-4 w-4 mr-2" />
                  Run Now
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleToggleEnabled}>
                  {task.enabled ? (
                    <>
                      <PowerOff className="h-4 w-4 mr-2" />
                      Disable
                    </>
                  ) : (
                    <>
                      <Power className="h-4 w-4 mr-2" />
                      Enable
                    </>
                  )}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={onDelete}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Info */}
        <div className="space-y-2 text-sm">
          {/* Schedule */}
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>{task.schedule_description || task.schedule}</span>
          </div>

          {/* Skill */}
          {task.skill && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Wand2 className="h-4 w-4" />
              <span>{task.skill}</span>
            </div>
          )}

          {/* Last run */}
          <div className="flex items-center justify-between pt-2 border-t">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Last run:</span>
              {task.last_status && (
                <span className={cn('flex items-center gap-1', getStatusBgColor(task.last_status), 'px-2 py-0.5 rounded-full text-xs')}>
                  {getStatusIcon(task.last_status)} {task.last_status}
                </span>
              )}
              <span className="text-muted-foreground">{formatRelativeTime(task.last_run)}</span>
            </div>
            {task.next_run && (
              <div className="text-muted-foreground">
                Next: {formatRelativeTime(task.next_run)}
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 mt-4">
          <Button variant="outline" size="sm" onClick={handleRun} disabled={isRunning}>
            <Play className="h-4 w-4 mr-1" />
            {isRunning ? 'Running...' : 'Run'}
          </Button>
          <Button variant="ghost" size="sm" asChild>
            <Link to={`/tasks/${task.id}`}>View Details</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

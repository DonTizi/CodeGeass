import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { RefreshCw, Filter, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';
import { useLogsStore, useTasksStore } from '@/stores';
import type { ExecutionStatus } from '@/types';
import {
  formatDate,
  formatDuration,
  formatRelativeTime,
  getStatusBgColor,
  getStatusIcon,
  cn,
} from '@/lib/utils';

export function Logs() {
  const { logs, stats, loading, statusFilter, taskFilter, fetchLogs, fetchStats, setStatusFilter, setTaskFilter } =
    useLogsStore();
  const { tasks, fetchTasks } = useTasksStore();

  useEffect(() => {
    fetchLogs();
    fetchStats();
    fetchTasks();
  }, [fetchLogs, fetchStats, fetchTasks]);

  useEffect(() => {
    fetchLogs();
  }, [statusFilter, taskFilter, fetchLogs]);

  const handleStatusChange = (value: string) => {
    setStatusFilter(value === 'all' ? null : (value as ExecutionStatus));
  };

  const handleTaskChange = (value: string) => {
    setTaskFilter(value === 'all' ? null : value);
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Executions</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_executions ?? 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Successful</CardTitle>
            <CheckCircle className="h-4 w-4 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-success">{stats?.successful ?? 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed / Timeout</CardTitle>
            <XCircle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">
              {(stats?.failed ?? 0) + (stats?.timeout ?? 0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatDuration(stats?.avg_duration_seconds ?? 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Filters:</span>
        </div>

        <Select value={statusFilter ?? 'all'} onValueChange={handleStatusChange}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="success">Success</SelectItem>
            <SelectItem value="failure">Failure</SelectItem>
            <SelectItem value="timeout">Timeout</SelectItem>
            <SelectItem value="running">Running</SelectItem>
          </SelectContent>
        </Select>

        <Select value={taskFilter ?? 'all'} onValueChange={handleTaskChange}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Task" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Tasks</SelectItem>
            {tasks
              .filter((task) => task.id && task.id.trim() !== '')
              .map((task) => (
                <SelectItem key={task.id} value={task.id}>
                  {task.name}
                </SelectItem>
              ))}
          </SelectContent>
        </Select>

        <Button variant="outline" size="sm" onClick={() => fetchLogs()} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Logs Table */}
      <Card>
        <CardHeader>
          <CardTitle>Execution Logs</CardTitle>
        </CardHeader>
        <CardContent>
          {logs.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No logs found</p>
          ) : (
            <div className="space-y-2">
              {logs.map((log, i) => (
                <div
                  key={`${log.session_id}-${i}`}
                  className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg hover:bg-muted/70 transition-colors"
                >
                  <span
                    className={cn(
                      'flex items-center justify-center h-6 w-6 rounded-full text-xs mt-0.5 flex-shrink-0',
                      getStatusBgColor(log.status)
                    )}
                  >
                    {getStatusIcon(log.status)}
                  </span>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge
                        variant={
                          log.status === 'success'
                            ? 'success'
                            : log.status === 'failure'
                            ? 'destructive'
                            : 'secondary'
                        }
                      >
                        {log.status.toUpperCase()}
                      </Badge>
                      {log.task_name && (
                        <Link
                          to={`/tasks/${log.task_id}`}
                          className="font-medium hover:text-primary"
                        >
                          {log.task_name}
                        </Link>
                      )}
                    </div>

                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>{formatDate(log.started_at)}</span>
                      {log.duration_seconds && (
                        <span>Duration: {formatDuration(log.duration_seconds)}</span>
                      )}
                      {log.exit_code !== null && <span>Exit: {log.exit_code}</span>}
                    </div>

                    {log.error && (
                      <p className="text-sm text-destructive mt-1 line-clamp-2">{log.error}</p>
                    )}

                    {log.clean_output && (
                      <details className="mt-2">
                        <summary className="text-sm text-muted-foreground cursor-pointer hover:text-foreground">
                          Show output
                        </summary>
                        <pre className="mt-2 p-2 bg-background rounded text-xs overflow-auto max-h-40 whitespace-pre-wrap">
                          {log.clean_output.slice(0, 1000)}
                          {log.clean_output.length > 1000 && '...'}
                        </pre>
                      </details>
                    )}
                  </div>

                  <span className="text-sm text-muted-foreground flex-shrink-0">
                    {formatRelativeTime(log.started_at)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

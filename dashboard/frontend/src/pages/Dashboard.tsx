import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ListTodo, CheckCircle, XCircle, Clock, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useTasksStore, useLogsStore, useSchedulerStore } from '@/stores';
import { formatRelativeTime, getStatusBgColor, getStatusIcon, cn } from '@/lib/utils';

export function Dashboard() {
  const { tasks, fetchTasks } = useTasksStore();
  const { stats, fetchStats } = useLogsStore();
  const { upcoming, fetchUpcoming, status } = useSchedulerStore();

  useEffect(() => {
    fetchTasks();
    fetchStats();
    fetchUpcoming(24);
  }, [fetchTasks, fetchStats, fetchUpcoming]);

  const enabledTasks = tasks.filter((t) => t.enabled);
  const recentTasks = [...tasks]
    .filter((t) => t.last_run)
    .sort((a, b) => new Date(b.last_run!).getTime() - new Date(a.last_run!).getTime())
    .slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tasks</CardTitle>
            <ListTodo className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{tasks.length}</div>
            <p className="text-xs text-muted-foreground">
              {enabledTasks.length} enabled
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Successful</CardTitle>
            <CheckCircle className="h-4 w-4 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.successful ?? 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.success_rate.toFixed(1) ?? 0}% success rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <XCircle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.failed ?? 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.timeout ?? 0} timeouts
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Due Tasks</CardTitle>
            <Clock className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{status?.due_tasks ?? 0}</div>
            <p className="text-xs text-muted-foreground">
              ready to run
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Upcoming Runs */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Upcoming Runs</CardTitle>
            <Link to="/tasks">
              <Button variant="ghost" size="sm">
                View all <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {upcoming.length === 0 ? (
              <p className="text-muted-foreground text-sm">No upcoming runs</p>
            ) : (
              <div className="space-y-3">
                {upcoming.slice(0, 5).map((run) => (
                  <div
                    key={`${run.task_id}-${run.next_run}`}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      <Link
                        to={`/tasks/${run.task_id}`}
                        className="font-medium hover:text-primary"
                      >
                        {run.task_name}
                      </Link>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {formatRelativeTime(run.next_run)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Executions */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Executions</CardTitle>
            <Link to="/logs">
              <Button variant="ghost" size="sm">
                View all <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {recentTasks.length === 0 ? (
              <p className="text-muted-foreground text-sm">No recent executions</p>
            ) : (
              <div className="space-y-3">
                {recentTasks.map((task) => (
                  <div key={task.id} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          'flex items-center justify-center h-5 w-5 rounded-full text-xs',
                          getStatusBgColor(task.last_status)
                        )}
                      >
                        {getStatusIcon(task.last_status)}
                      </span>
                      <Link
                        to={`/tasks/${task.id}`}
                        className="font-medium hover:text-primary"
                      >
                        {task.name}
                      </Link>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {formatRelativeTime(task.last_run)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <Link to="/tasks">
            <Button>
              <ListTodo className="h-4 w-4 mr-2" />
              Manage Tasks
            </Button>
          </Link>
          <Link to="/logs">
            <Button variant="outline">
              View Logs
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}

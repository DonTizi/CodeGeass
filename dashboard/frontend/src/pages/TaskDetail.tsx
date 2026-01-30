import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Play,
  Edit,
  Trash2,
  Clock,
  Wand2,
  Folder,
  Timer,
  BarChart3,
  CheckCircle,
  Square,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Switch } from '@/components/ui/Switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { TaskForm } from '@/components/tasks/TaskForm';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/AlertDialog';
import { useTasksStore, useLogsStore, useExecutionsStore } from '@/stores';
import { toast } from '@/components/ui/Toaster';
import type { TaskCreate, TaskUpdate, ExecutionResult } from '@/types';
import {
  formatRelativeTime,
  formatDate,
  formatDuration,
  getStatusBgColor,
  getStatusIcon,
  cn,
} from '@/lib/utils';
import { ActiveExecutionBadge, ExecutionMonitor } from '@/components/executions';

export function TaskDetail() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const {
    selectedTask: task,
    taskStats,
    fetchTask,
    fetchTaskStats,
    updateTask,
    deleteTask,
    enableTask,
    disableTask,
    runTask,
    stopTask,
  } = useTasksStore();
  const { fetchTaskLogs } = useLogsStore();

  const [logs, setLogs] = useState<ExecutionResult[]>([]);
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [running, setRunning] = useState(false);
  const [stopping, setStopping] = useState(false);

  // Get active execution for this task
  const activeExecution = useExecutionsStore((state) =>
    taskId ? state.getByTaskId(taskId) : undefined
  );
  const isRunning = !!activeExecution;

  useEffect(() => {
    if (taskId) {
      fetchTask(taskId);
      fetchTaskStats(taskId);
      fetchTaskLogs(taskId, 20).then(setLogs);
    }
  }, [taskId, fetchTask, fetchTaskStats, fetchTaskLogs]);

  if (!task) {
    // Show execution monitor even while task is loading
    if (isRunning && activeExecution) {
      return (
        <div className="space-y-6">
          <ExecutionMonitor execution={activeExecution} />
          <div className="flex items-center justify-center h-32">
            <p className="text-muted-foreground">Loading task details...</p>
          </div>
        </div>
      );
    }
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading task...</p>
      </div>
    );
  }

  const stats = taskStats[task.id];

  const handleToggleEnabled = async () => {
    try {
      if (task.enabled) {
        await disableTask(task.id);
        toast({ title: 'Task disabled', variant: 'default' });
      } else {
        await enableTask(task.id);
        toast({ title: 'Task enabled', variant: 'success' });
      }
    } catch {
      toast({ title: 'Failed to toggle task', variant: 'destructive' });
    }
  };

  const handleRun = async () => {
    setRunning(true);
    try {
      const result = await runTask(task.id);
      if (result.status === 'success') {
        toast({ title: 'Task completed successfully', variant: 'success' });
      } else {
        toast({ title: `Task ${result.status}`, variant: 'destructive' });
      }
      // Refresh logs
      const newLogs = await fetchTaskLogs(task.id, 20);
      setLogs(newLogs);
    } catch (e) {
      toast({
        title: 'Failed to run task',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setRunning(false);
    }
  };

  const handleStop = async () => {
    setStopping(true);
    try {
      await stopTask(task.id);
      toast({ title: 'Task stopped', variant: 'default' });
    } catch (e) {
      toast({
        title: 'Failed to stop task',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setStopping(false);
    }
  };

  const handleUpdate = async (data: TaskCreate) => {
    try {
      await updateTask(task.id, data as TaskUpdate);
      toast({ title: 'Task updated', variant: 'success' });
    } catch (e) {
      toast({
        title: 'Failed to update task',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      });
      throw e;
    }
  };

  const handleDelete = async () => {
    try {
      await deleteTask(task.id);
      toast({ title: 'Task deleted', variant: 'default' });
      navigate('/tasks');
    } catch (e) {
      toast({
        title: 'Failed to delete task',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Link to="/tasks">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-serif font-bold">{task.name}</h1>
              {isRunning ? (
                <ActiveExecutionBadge execution={activeExecution} showDuration />
              ) : (
                <Badge variant={task.enabled ? 'success' : 'secondary'}>
                  {task.enabled ? 'Enabled' : 'Disabled'}
                </Badge>
              )}
            </div>
            <p className="text-muted-foreground">
              {task.schedule_description || task.schedule}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Switch checked={task.enabled} onCheckedChange={handleToggleEnabled} />
          <Button variant="outline" size="sm" onClick={() => setEditOpen(true)}>
            <Edit className="h-4 w-4 mr-1" />
            Edit
          </Button>
          {isRunning ? (
            <Button
              size="sm"
              variant="destructive"
              onClick={handleStop}
              disabled={stopping}
            >
              <Square className="h-4 w-4 mr-1" />
              {stopping ? 'Stopping...' : 'Stop'}
            </Button>
          ) : (
            <Button size="sm" onClick={handleRun} disabled={running}>
              <Play className="h-4 w-4 mr-1" />
              {running ? 'Running...' : 'Run Now'}
            </Button>
          )}
        </div>
      </div>

      {/* Show execution monitor when task is running */}
      {isRunning && activeExecution && (
        <ExecutionMonitor execution={activeExecution} className="mb-6" />
      )}

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="logs">Execution Logs</TabsTrigger>
          <TabsTrigger value="config">Configuration</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Stats */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_runs ?? 0}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
                <CheckCircle className="h-4 w-4 text-success" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.success_rate.toFixed(1) ?? 0}%
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
                <Timer className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatDuration(stats?.avg_duration_seconds ?? 0)}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Last Run</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatRelativeTime(task.last_run)}
                </div>
                {task.last_status && (
                  <Badge
                    variant={
                      task.last_status === 'success'
                        ? 'success'
                        : task.last_status === 'failure'
                        ? 'destructive'
                        : 'secondary'
                    }
                    className="mt-1"
                  >
                    {task.last_status}
                  </Badge>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Info Cards */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Schedule</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <code className="bg-muted px-2 py-1 rounded">{task.schedule}</code>
                </div>
                {task.schedule_description && (
                  <p className="text-sm text-muted-foreground">
                    {task.schedule_description}
                  </p>
                )}
                {task.next_run && (
                  <p className="text-sm">
                    Next run: <strong>{formatRelativeTime(task.next_run)}</strong>
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Execution</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {task.skill ? (
                  <div className="flex items-center gap-2">
                    <Wand2 className="h-4 w-4 text-muted-foreground" />
                    <span>Skill: <strong>{task.skill}</strong></span>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Uses direct prompt</p>
                )}
                <div className="flex items-center gap-2">
                  <Folder className="h-4 w-4 text-muted-foreground" />
                  <code className="text-xs bg-muted px-2 py-1 rounded truncate max-w-full">
                    {task.working_dir}
                  </code>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{task.model}</Badge>
                  <span className="text-sm text-muted-foreground">
                    Timeout: {task.timeout}s
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Executions</CardTitle>
            </CardHeader>
            <CardContent>
              {logs.length === 0 ? (
                <p className="text-muted-foreground">No execution logs yet</p>
              ) : (
                <div className="space-y-3">
                  {logs.map((log, i) => (
                    <div
                      key={`${log.session_id}-${i}`}
                      className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg"
                    >
                      <span
                        className={cn(
                          'flex items-center justify-center h-6 w-6 rounded-full text-xs mt-0.5',
                          getStatusBgColor(log.status)
                        )}
                      >
                        {getStatusIcon(log.status)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="font-medium capitalize">{log.status}</span>
                          <span className="text-sm text-muted-foreground">
                            {formatDate(log.started_at)}
                          </span>
                        </div>
                        {log.duration_seconds && (
                          <p className="text-sm text-muted-foreground">
                            Duration: {formatDuration(log.duration_seconds)}
                          </p>
                        )}
                        {log.error && (
                          <p className="text-sm text-destructive mt-1 truncate">
                            {log.error}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="config" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Task Configuration</CardTitle>
              <Button variant="destructive" size="sm" onClick={() => setDeleteOpen(true)}>
                <Trash2 className="h-4 w-4 mr-1" />
                Delete Task
              </Button>
            </CardHeader>
            <CardContent>
              <pre className="bg-muted p-4 rounded-lg overflow-auto text-sm">
                {JSON.stringify(task, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Dialog */}
      <TaskForm
        open={editOpen}
        onOpenChange={setEditOpen}
        onSubmit={handleUpdate}
        initialData={task}
        isEdit
      />

      {/* Delete Confirmation */}
      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Task</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{task.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

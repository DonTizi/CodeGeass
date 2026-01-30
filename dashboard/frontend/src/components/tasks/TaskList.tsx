import { useEffect, useState, useMemo } from 'react';
import { Plus, RefreshCw } from 'lucide-react';
import { useTasksStore, useProjectsStore } from '@/stores';
import { TaskCard } from './TaskCard';
import { TaskForm } from './TaskForm';
import { Button } from '@/components/ui/Button';
import { toast } from '@/components/ui/Toaster';
import type { TaskCreate, TaskWithProject } from '@/types';
import { api } from '@/lib/api';
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

export function TaskList() {
  const { tasks, loading, error, fetchTasks, createTask, deleteTask } = useTasksStore();
  const { projects, selectedProjectId, fetchProjects } = useProjectsStore();
  const [formOpen, setFormOpen] = useState(false);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [multiProjectTasks, setMultiProjectTasks] = useState<TaskWithProject[]>([]);
  const [loadingMultiProject, setLoadingMultiProject] = useState(false);

  // Fetch projects on mount
  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // Determine if we're in multi-project mode
  const hasMultipleProjects = projects.length > 1;
  const showAllProjects = selectedProjectId === null && hasMultipleProjects;

  // Fetch tasks based on mode
  useEffect(() => {
    if (showAllProjects) {
      // Multi-project mode: fetch aggregated tasks
      setLoadingMultiProject(true);
      api.projects.getAllTasks(false, false)
        .then(setMultiProjectTasks)
        .catch(console.error)
        .finally(() => setLoadingMultiProject(false));
    } else {
      // Single project mode: use regular task fetch
      fetchTasks();
    }
  }, [fetchTasks, showAllProjects, selectedProjectId]);

  // Get the display tasks
  const displayTasks = useMemo(() => {
    if (showAllProjects) {
      return multiProjectTasks;
    }
    return tasks;
  }, [showAllProjects, multiProjectTasks, tasks]);

  const isLoading = showAllProjects ? loadingMultiProject : loading;

  const handleCreate = async (data: TaskCreate) => {
    try {
      await createTask(data);
      toast({ title: 'Task created', variant: 'success' });
    } catch (e) {
      toast({
        title: 'Failed to create task',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      });
      throw e;
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await deleteTask(deleteId);
      toast({ title: 'Task deleted', variant: 'default' });
    } catch (e) {
      toast({
        title: 'Failed to delete task',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setDeleteId(null);
    }
  };

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-destructive mb-4">{error}</p>
        <Button onClick={() => fetchTasks()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-muted-foreground">
          {displayTasks.length} task{displayTasks.length !== 1 ? 's' : ''} configured
          {showAllProjects && ' across all projects'}
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => showAllProjects
              ? api.projects.getAllTasks(false, false).then(setMultiProjectTasks)
              : fetchTasks()
            }
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {!showAllProjects && (
            <Button size="sm" onClick={() => setFormOpen(true)}>
              <Plus className="h-4 w-4 mr-1" />
              New Task
            </Button>
          )}
        </div>
      </div>

      {/* Task Grid */}
      {displayTasks.length === 0 ? (
        <div className="text-center py-12 bg-muted/50 rounded-lg">
          <p className="text-muted-foreground mb-4">
            {showAllProjects ? 'No tasks found across projects' : 'No tasks configured yet'}
          </p>
          {!showAllProjects && (
            <Button onClick={() => setFormOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create your first task
            </Button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {displayTasks.map((task) => (
            <TaskCard
              key={`${(task as TaskWithProject).project_id || 'local'}-${task.id}`}
              task={task}
              onDelete={() => setDeleteId(task.id)}
              projectName={showAllProjects ? (task as TaskWithProject).project_name : undefined}
            />
          ))}
        </div>
      )}

      {/* Create Form */}
      <TaskForm open={formOpen} onOpenChange={setFormOpen} onSubmit={handleCreate} />

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Task</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this task? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

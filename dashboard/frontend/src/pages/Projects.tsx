import { useEffect, useState } from 'react';
import { Plus, RefreshCw, Star, FolderOpen, Trash2, MoreVertical, Power, PowerOff, FolderSearch } from 'lucide-react';
import { useProjectsStore } from '@/stores';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { toast } from '@/components/ui/Toaster';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog';
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';
import type { Project, ProjectCreate } from '@/types';
import { api } from '@/lib/api';

export function Projects() {
  const {
    projects,
    loading,
    fetchProjects,
    addProject,
    removeProject,
    setDefaultProject,
    enableProject,
    disableProject,
  } = useProjectsStore();

  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [newProjectPath, setNewProjectPath] = useState('');
  const [newProjectName, setNewProjectName] = useState('');
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [browsing, setBrowsing] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleBrowseFolder = async () => {
    setBrowsing(true);
    try {
      const result = await api.filesystem.pickFolder();
      if (result.path) {
        setNewProjectPath(result.path);
      } else if (result.error) {
        toast({ title: 'Browse failed', description: result.error, variant: 'destructive' });
      }
    } catch (e) {
      toast({
        title: 'Browse failed',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setBrowsing(false);
    }
  };

  const handleAddProject = async () => {
    if (!newProjectPath.trim()) {
      toast({ title: 'Path is required', variant: 'destructive' });
      return;
    }

    try {
      const data: ProjectCreate = {
        path: newProjectPath,
        name: newProjectName || undefined,
      };
      await addProject(data);
      toast({ title: 'Project added successfully', variant: 'success' });
      setAddDialogOpen(false);
      setNewProjectPath('');
      setNewProjectName('');
    } catch (e) {
      toast({
        title: 'Failed to add project',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const handleRemove = async () => {
    if (!deleteId) return;
    try {
      await removeProject(deleteId);
      toast({ title: 'Project removed', variant: 'default' });
    } catch (e) {
      toast({
        title: 'Failed to remove project',
        description: e instanceof Error ? e.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setDeleteId(null);
    }
  };

  const handleSetDefault = async (projectId: string) => {
    try {
      await setDefaultProject(projectId);
      toast({ title: 'Default project updated', variant: 'success' });
    } catch (e) {
      toast({ title: 'Failed to set default', variant: 'destructive' });
    }
  };

  const handleToggleEnabled = async (project: Project) => {
    try {
      if (project.enabled) {
        await disableProject(project.id);
        toast({ title: 'Project disabled', variant: 'default' });
      } else {
        await enableProject(project.id);
        toast({ title: 'Project enabled', variant: 'success' });
      }
    } catch (e) {
      toast({ title: 'Failed to toggle project', variant: 'destructive' });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-muted-foreground">
          {projects.length} project{projects.length !== 1 ? 's' : ''} registered
        </p>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => fetchProjects()} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button size="sm" onClick={() => setAddDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-1" />
            Add Project
          </Button>
        </div>
      </div>

      {/* Project Grid */}
      {projects.length === 0 ? (
        <div className="text-center py-12 bg-muted/50 rounded-lg">
          <FolderOpen className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground mb-4">No projects registered yet</p>
          <Button onClick={() => setAddDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Register your first project
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Card key={project.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-lg">{project.name}</CardTitle>
                    {project.is_default && (
                      <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                    )}
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {!project.is_default && (
                        <DropdownMenuItem onClick={() => handleSetDefault(project.id)}>
                          <Star className="h-4 w-4 mr-2" />
                          Set as Default
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuItem onClick={() => handleToggleEnabled(project)}>
                        {project.enabled ? (
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
                        onClick={() => setDeleteId(project.id)}
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Remove
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-2">
                  <Badge variant={project.enabled ? 'success' : 'secondary'}>
                    {project.enabled ? 'Enabled' : 'Disabled'}
                  </Badge>
                  {!project.exists && (
                    <Badge variant="destructive">Path not found</Badge>
                  )}
                  {project.exists && !project.is_initialized && (
                    <Badge variant="outline">Not initialized</Badge>
                  )}
                </div>

                <div className="text-sm text-muted-foreground truncate" title={project.path}>
                  {project.path}
                </div>

                {project.description && (
                  <p className="text-sm text-muted-foreground">{project.description}</p>
                )}

                <div className="flex items-center gap-4 pt-2 border-t text-sm">
                  <div>
                    <span className="text-muted-foreground">Tasks: </span>
                    <span className="font-medium">{project.task_count}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Skills: </span>
                    <span className="font-medium">{project.skill_count}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Add Project Dialog */}
      <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Project</DialogTitle>
            <DialogDescription>
              Register an existing project directory with CodeGeass.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="path">Project Path</Label>
              <div className="flex gap-2">
                <Input
                  id="path"
                  placeholder="/home/user/projects/my-project"
                  value={newProjectPath}
                  onChange={(e) => setNewProjectPath(e.target.value)}
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleBrowseFolder}
                  disabled={browsing}
                  title="Browse folders"
                >
                  <FolderSearch className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="name">Project Name (optional)</Label>
              <Input
                id="name"
                placeholder="Defaults to directory name"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddProject}>Add Project</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove Project</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove this project from CodeGeass?
              This only unregisters the project - your files will not be deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRemove}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

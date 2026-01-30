import { useEffect } from 'react';
import { FolderGit2, Star } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { useProjectsStore } from '@/stores';

export function ProjectSelector() {
  const { projects, selectedProjectId, fetchProjects, selectProject } =
    useProjectsStore();

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // Don't render if no projects registered
  if (projects.length === 0) {
    return null;
  }

  const selectedProject =
    selectedProjectId === null
      ? null
      : projects.find((p) => p.id === selectedProjectId);

  return (
    <Select
      value={selectedProjectId || 'all'}
      onValueChange={(value) => selectProject(value === 'all' ? null : value)}
    >
      <SelectTrigger className="w-[200px] h-9">
        <div className="flex items-center gap-2">
          <FolderGit2 className="h-4 w-4 text-muted-foreground" />
          <SelectValue placeholder="Select project">
            {selectedProject ? (
              <span className="flex items-center gap-2">
                {selectedProject.name}
                {selectedProject.is_default && (
                  <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />
                )}
              </span>
            ) : (
              'All Projects'
            )}
          </SelectValue>
        </div>
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">
          <div className="flex items-center justify-between w-full">
            <span>All Projects</span>
            <Badge variant="secondary" className="ml-2 text-xs">
              {projects.reduce((sum, p) => sum + p.task_count, 0)}
            </Badge>
          </div>
        </SelectItem>
        {projects.map((project) => (
          <SelectItem key={project.id} value={project.id}>
            <div className="flex items-center justify-between w-full gap-2">
              <span className="flex items-center gap-1">
                {project.name}
                {project.is_default && (
                  <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />
                )}
              </span>
              <Badge
                variant={project.enabled ? 'secondary' : 'outline'}
                className="ml-2 text-xs"
              >
                {project.task_count}
              </Badge>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

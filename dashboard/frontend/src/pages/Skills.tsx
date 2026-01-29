import { useEffect, useState } from 'react';
import { RefreshCw, Wand2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog';
import { useSkillsStore } from '@/stores';
import { toast } from '@/components/ui/Toaster';

export function Skills() {
  const { skills, selectedSkill, loading, fetchSkills, fetchSkill, reloadSkills } =
    useSkillsStore();
  const [detailOpen, setDetailOpen] = useState(false);

  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  const handleReload = async () => {
    try {
      await reloadSkills();
      toast({ title: 'Skills reloaded', variant: 'success' });
    } catch {
      toast({ title: 'Failed to reload skills', variant: 'destructive' });
    }
  };

  const handleViewSkill = async (name: string) => {
    await fetchSkill(name);
    setDetailOpen(true);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-muted-foreground">
          {skills.length} skill{skills.length !== 1 ? 's' : ''} available
        </p>
        <Button variant="outline" size="sm" onClick={handleReload} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
          Reload
        </Button>
      </div>

      {/* Skills Grid */}
      {skills.length === 0 ? (
        <div className="text-center py-12 bg-muted/50 rounded-lg">
          <Wand2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground mb-2">No skills found</p>
          <p className="text-sm text-muted-foreground">
            Add skills to <code>.claude/skills/</code> directory
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {skills.map((skill) => (
            <Card key={skill.name} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Wand2 className="h-5 w-5 text-primary" />
                    <CardTitle className="text-lg">{skill.name}</CardTitle>
                  </div>
                  <Badge variant={skill.context === 'fork' ? 'secondary' : 'outline'}>
                    {skill.context}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                  {skill.description || 'No description'}
                </p>
                <div className="flex items-center justify-between">
                  {skill.has_agent && (
                    <Badge variant="outline" className="text-xs">
                      Has Agent
                    </Badge>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleViewSkill(skill.name)}
                  >
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Skill Detail Dialog */}
      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Wand2 className="h-5 w-5 text-primary" />
              {selectedSkill?.name}
            </DialogTitle>
          </DialogHeader>

          {selectedSkill && (
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium mb-1">Description</h4>
                <p className="text-muted-foreground">
                  {selectedSkill.description || 'No description'}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium mb-1">Context</h4>
                  <Badge variant={selectedSkill.context === 'fork' ? 'secondary' : 'outline'}>
                    {selectedSkill.context}
                  </Badge>
                </div>
                {selectedSkill.agent && (
                  <div>
                    <h4 className="text-sm font-medium mb-1">Agent</h4>
                    <code className="text-sm bg-muted px-2 py-1 rounded">
                      {selectedSkill.agent}
                    </code>
                  </div>
                )}
              </div>

              {selectedSkill.allowed_tools.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-1">Allowed Tools</h4>
                  <div className="flex flex-wrap gap-1">
                    {selectedSkill.allowed_tools.map((tool) => (
                      <Badge key={tool} variant="outline" className="text-xs">
                        {tool}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {selectedSkill.dynamic_commands.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-1">Dynamic Commands</h4>
                  <div className="flex flex-wrap gap-1">
                    {selectedSkill.dynamic_commands.map((cmd) => (
                      <Badge key={cmd} variant="secondary" className="text-xs font-mono">
                        {cmd}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <h4 className="text-sm font-medium mb-1">Path</h4>
                <code className="text-xs bg-muted px-2 py-1 rounded block truncate">
                  {selectedSkill.path}
                </code>
              </div>

              {selectedSkill.content && (
                <div>
                  <h4 className="text-sm font-medium mb-1">Content Preview</h4>
                  <pre className="bg-muted p-4 rounded-lg overflow-auto text-xs max-h-64">
                    {selectedSkill.content.slice(0, 2000)}
                    {selectedSkill.content.length > 2000 && '...'}
                  </pre>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

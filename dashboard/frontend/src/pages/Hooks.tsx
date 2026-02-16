import { useEffect, useState } from 'react';
import { RefreshCw, Anchor, Plus, Trash2, CheckCircle, XCircle, Download } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
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
import { useHooksStore } from '@/stores';
import { toast } from '@/components/ui/Toaster';
import type { HookSummary, HookMatcher } from '@/types';

export function Hooks() {
  const {
    hooks,
    selectedHook,
    templates,
    loading,
    fetchHooks,
    fetchHook,
    fetchTemplates,
    createHook,
    deleteHook,
    initTemplates,
    validateHook,
  } = useHooksStore();

  const [detailOpen, setDetailOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [hookToDelete, setHookToDelete] = useState<string | null>(null);
  const [newTagName, setNewTagName] = useState('');
  const [newTagDescription, setNewTagDescription] = useState('');
  const [isGlobal, setIsGlobal] = useState(false);
  const [validationResults, setValidationResults] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetchHooks();
    fetchTemplates();
  }, [fetchHooks, fetchTemplates]);

  const handleViewHook = async (tag: string) => {
    await fetchHook(tag);
    setDetailOpen(true);
  };

  const handleInitTemplates = async () => {
    try {
      const initialized = await initTemplates();
      if (initialized.length > 0) {
        toast({
          title: `Initialized ${initialized.length} template(s)`,
          description: initialized.join(', '),
          variant: 'success',
        });
      } else {
        toast({ title: 'All templates already exist', variant: 'default' });
      }
    } catch {
      toast({ title: 'Failed to initialize templates', variant: 'destructive' });
    }
  };

  const handleCreate = async () => {
    if (!newTagName.trim()) {
      toast({ title: 'Tag name is required', variant: 'destructive' });
      return;
    }

    try {
      await createHook({
        tag: newTagName.trim(),
        description: newTagDescription.trim() || undefined,
        global_scope: isGlobal,
      });
      toast({ title: `Created hook: ${newTagName}`, variant: 'success' });
      setCreateOpen(false);
      setNewTagName('');
      setNewTagDescription('');
      setIsGlobal(false);
    } catch {
      toast({ title: 'Failed to create hook', variant: 'destructive' });
    }
  };

  const handleDelete = async () => {
    if (!hookToDelete) return;

    try {
      await deleteHook(hookToDelete);
      toast({ title: `Deleted hook: ${hookToDelete}`, variant: 'success' });
      setDeleteOpen(false);
      setHookToDelete(null);
    } catch {
      toast({ title: 'Failed to delete hook', variant: 'destructive' });
    }
  };

  const handleValidate = async (tag: string) => {
    try {
      const result = await validateHook(tag);
      setValidationResults((prev) => ({ ...prev, [tag]: result.valid }));
      if (result.valid) {
        toast({ title: `${tag} is valid`, variant: 'success' });
      } else {
        toast({
          title: `${tag} has errors`,
          description: result.errors.join(', '),
          variant: 'destructive',
        });
      }
    } catch {
      toast({ title: 'Failed to validate hook', variant: 'destructive' });
    }
  };

  const confirmDelete = (tag: string) => {
    setHookToDelete(tag);
    setDeleteOpen(true);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-muted-foreground">
          {hooks.length} hook{hooks.length !== 1 ? 's' : ''} configured
        </p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleInitTemplates} disabled={loading}>
            <Download className="h-4 w-4 mr-1" />
            Init Templates
          </Button>
          <Button variant="outline" size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4 mr-1" />
            Create Hook
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchHooks()}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Templates Info */}
      {templates.length > 0 && (
        <div className="text-sm text-muted-foreground bg-muted/50 p-3 rounded-lg">
          <span className="font-medium">Available templates:</span>{' '}
          {templates.join(', ')}
        </div>
      )}

      {/* Hooks Grid */}
      {hooks.length === 0 ? (
        <div className="text-center py-12 bg-muted/50 rounded-lg">
          <Anchor className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground mb-2">No hooks configured</p>
          <p className="text-sm text-muted-foreground mb-4">
            Initialize built-in templates or create a custom hook
          </p>
          <Button variant="default" onClick={handleInitTemplates}>
            <Download className="h-4 w-4 mr-2" />
            Initialize Templates
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {hooks.map((hook: HookSummary) => (
            <Card key={hook.tag} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Anchor className="h-5 w-5 text-primary" />
                    <CardTitle className="text-lg">{hook.tag}</CardTitle>
                  </div>
                  <div className="flex items-center gap-1">
                    <Badge variant={hook.location === 'project' ? 'default' : 'secondary'}>
                      {hook.location}
                    </Badge>
                    {validationResults[hook.tag] !== undefined && (
                      validationResults[hook.tag] ? (
                        <CheckCircle className="h-4 w-4 text-success" />
                      ) : (
                        <XCircle className="h-4 w-4 text-destructive" />
                      )
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                  {hook.description || 'No description'}
                </p>

                {hook.events.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {hook.events.slice(0, 3).map((event) => (
                      <Badge key={event} variant="outline" className="text-xs">
                        {event}
                      </Badge>
                    ))}
                    {hook.events.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{hook.events.length - 3} more
                      </Badge>
                    )}
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleValidate(hook.tag)}
                  >
                    Validate
                  </Button>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleViewHook(hook.tag)}
                    >
                      View
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive"
                      onClick={() => confirmDelete(hook.tag)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Hook Detail Dialog */}
      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Anchor className="h-5 w-5 text-primary" />
              {selectedHook?.tag}
            </DialogTitle>
          </DialogHeader>

          {selectedHook && (
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium mb-1">Description</h4>
                <p className="text-muted-foreground">
                  {selectedHook.description || 'No description'}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium mb-1">Location</h4>
                  <Badge variant={selectedHook.location === 'project' ? 'default' : 'secondary'}>
                    {selectedHook.location}
                  </Badge>
                </div>
              </div>

              {/* Hook Events */}
              {Object.entries(selectedHook.hooks || {}).map(([event, matchers]) => (
                <div key={event} className="border rounded-lg p-3">
                  <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                    <Badge variant="outline">{event}</Badge>
                    <span className="text-muted-foreground text-xs">
                      {(matchers as HookMatcher[]).length} matcher(s)
                    </span>
                  </h4>
                  <div className="space-y-2">
                    {(matchers as HookMatcher[]).map((matcher, i) => (
                      <div key={i} className="bg-muted/50 rounded p-2 text-sm">
                        <div className="font-mono text-xs text-muted-foreground mb-1">
                          Matcher: {matcher.matcher || '(all tools)'}
                        </div>
                        {matcher.hooks.map((handler, j) => (
                          <div key={j} className="ml-2 text-xs">
                            <span className="text-primary">{handler.type}:</span>{' '}
                            {handler.type === 'command' && (
                              <code className="bg-background px-1 rounded">
                                {handler.command?.slice(0, 60)}
                                {(handler.command?.length || 0) > 60 && '...'}
                              </code>
                            )}
                            {handler.type === 'prompt' && (
                              <span className="italic">
                                {handler.prompt?.slice(0, 40)}...
                              </span>
                            )}
                            {handler.type === 'agent' && <span>Agent handler</span>}
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              ))}

              {Object.keys(selectedHook.hooks || {}).length === 0 && (
                <p className="text-muted-foreground text-center py-4">
                  No hooks configured for this tag
                </p>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Create Hook Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Hook</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-1 block">Tag Name</label>
              <Input
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                placeholder="e.g., my-custom-hook"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Description</label>
              <Input
                value={newTagDescription}
                onChange={(e) => setNewTagDescription(e.target.value)}
                placeholder="What this hook does..."
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="isGlobal"
                checked={isGlobal}
                onChange={(e) => setIsGlobal(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="isGlobal" className="text-sm">
                Create as global hook (available in all projects)
              </label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={loading}>
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Hook</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the hook "{hookToDelete}"? This action cannot
              be undone.
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

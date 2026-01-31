import { X } from 'lucide-react';
import { useFilterStore } from '@/stores';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export function FilterChips() {
  const {
    search,
    tags,
    status,
    model,
    enabled,
    setSearch,
    removeTag,
    setStatus,
    setModel,
    setEnabled,
    clearFilters,
    hasActiveFilters,
  } = useFilterStore();

  if (!hasActiveFilters()) return null;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm text-muted-foreground">Active filters:</span>

      {search && (
        <Badge variant="secondary" className="gap-1">
          search: {search}
          <button onClick={() => setSearch('')} className="ml-1 hover:text-destructive">
            <X className="h-3 w-3" />
          </button>
        </Badge>
      )}

      {tags.map((tag) => (
        <Badge key={tag} variant="secondary" className="gap-1">
          tag: {tag}
          <button onClick={() => removeTag(tag)} className="ml-1 hover:text-destructive">
            <X className="h-3 w-3" />
          </button>
        </Badge>
      ))}

      {status && (
        <Badge variant="secondary" className="gap-1">
          status: {status}
          <button onClick={() => setStatus(undefined)} className="ml-1 hover:text-destructive">
            <X className="h-3 w-3" />
          </button>
        </Badge>
      )}

      {model && (
        <Badge variant="secondary" className="gap-1">
          model: {model}
          <button onClick={() => setModel(undefined)} className="ml-1 hover:text-destructive">
            <X className="h-3 w-3" />
          </button>
        </Badge>
      )}

      {enabled !== undefined && (
        <Badge variant="secondary" className="gap-1">
          {enabled ? 'enabled' : 'disabled'}
          <button onClick={() => setEnabled(undefined)} className="ml-1 hover:text-destructive">
            <X className="h-3 w-3" />
          </button>
        </Badge>
      )}

      <Button
        variant="ghost"
        size="sm"
        onClick={clearFilters}
        className="h-6 px-2 text-xs"
      >
        Clear all
      </Button>
    </div>
  );
}

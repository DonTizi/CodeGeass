import { Filter } from 'lucide-react';
import { useFilterStore, useTasksStore } from '@/stores';
import { Button } from '@/components/ui/Button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
} from '@/components/ui/DropdownMenu';

export function FilterPanel() {
  const { allTags } = useTasksStore();
  const {
    tags,
    status,
    model,
    enabled,
    addTag,
    removeTag,
    setStatus,
    setModel,
    setEnabled,
  } = useFilterStore();

  const activeFiltersCount =
    (tags.length > 0 ? 1 : 0) +
    (status ? 1 : 0) +
    (model ? 1 : 0) +
    (enabled !== undefined ? 1 : 0);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm">
          <Filter className="h-4 w-4 mr-1" />
          Filters
          {activeFiltersCount > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-xs bg-primary text-primary-foreground rounded-full">
              {activeFiltersCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        {/* Status Filter */}
        <DropdownMenuGroup>
          <DropdownMenuLabel>Status</DropdownMenuLabel>
          <DropdownMenuCheckboxItem
            checked={status === 'success'}
            onCheckedChange={(checked) => setStatus(checked ? 'success' : undefined)}
          >
            Success
          </DropdownMenuCheckboxItem>
          <DropdownMenuCheckboxItem
            checked={status === 'failed'}
            onCheckedChange={(checked) => setStatus(checked ? 'failed' : undefined)}
          >
            Failed
          </DropdownMenuCheckboxItem>
          <DropdownMenuCheckboxItem
            checked={status === 'never_run'}
            onCheckedChange={(checked) => setStatus(checked ? 'never_run' : undefined)}
          >
            Never Run
          </DropdownMenuCheckboxItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator />

        {/* Model Filter */}
        <DropdownMenuGroup>
          <DropdownMenuLabel>Model</DropdownMenuLabel>
          <DropdownMenuCheckboxItem
            checked={model === 'sonnet'}
            onCheckedChange={(checked) => setModel(checked ? 'sonnet' : undefined)}
          >
            Sonnet
          </DropdownMenuCheckboxItem>
          <DropdownMenuCheckboxItem
            checked={model === 'haiku'}
            onCheckedChange={(checked) => setModel(checked ? 'haiku' : undefined)}
          >
            Haiku
          </DropdownMenuCheckboxItem>
          <DropdownMenuCheckboxItem
            checked={model === 'opus'}
            onCheckedChange={(checked) => setModel(checked ? 'opus' : undefined)}
          >
            Opus
          </DropdownMenuCheckboxItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator />

        {/* Enabled Filter */}
        <DropdownMenuGroup>
          <DropdownMenuLabel>State</DropdownMenuLabel>
          <DropdownMenuCheckboxItem
            checked={enabled === true}
            onCheckedChange={(checked) => setEnabled(checked ? true : undefined)}
          >
            Enabled
          </DropdownMenuCheckboxItem>
          <DropdownMenuCheckboxItem
            checked={enabled === false}
            onCheckedChange={(checked) => setEnabled(checked ? false : undefined)}
          >
            Disabled
          </DropdownMenuCheckboxItem>
        </DropdownMenuGroup>

        {/* Tags Filter */}
        {allTags.length > 0 && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuLabel>Tags</DropdownMenuLabel>
              {allTags.map((tag) => (
                <DropdownMenuCheckboxItem
                  key={tag}
                  checked={tags.includes(tag)}
                  onCheckedChange={(checked) =>
                    checked ? addTag(tag) : removeTag(tag)
                  }
                >
                  {tag}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuGroup>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

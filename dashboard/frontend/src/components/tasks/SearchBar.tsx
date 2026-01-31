import { Search, X } from 'lucide-react';
import { useFilterStore } from '@/stores';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

export function SearchBar() {
  const { search, setSearch } = useFilterStore();

  return (
    <div className="relative flex-1 max-w-md">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
      <Input
        type="text"
        placeholder="Search tasks..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="pl-9 pr-8"
      />
      {search && (
        <Button
          variant="ghost"
          size="sm"
          className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6 p-0"
          onClick={() => setSearch('')}
        >
          <X className="h-3 w-3" />
        </Button>
      )}
    </div>
  );
}

import { NavLink } from 'react-router-dom';
import { LayoutDashboard, ListTodo, Wand2, FileText, Clock, Settings, FolderGit2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSchedulerStore } from '@/stores';
import { useEffect } from 'react';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/tasks', icon: ListTodo, label: 'Tasks' },
  { to: '/skills', icon: Wand2, label: 'Skills' },
  { to: '/logs', icon: FileText, label: 'Logs' },
  { to: '/projects', icon: FolderGit2, label: 'Projects' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export function Sidebar() {
  const { status, fetchStatus } = useSchedulerStore();

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  return (
    <aside className="w-64 border-r bg-card flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b">
        <div className="flex items-center -ml-5">
          <img src="/logo.png" alt="CodeGeass" className="w-28 h-auto -mr-2" />
          <div>
            <h1 className="text-xl font-serif font-bold text-foreground">
              Code<span className="text-primary">Geass</span>
            </h1>
            <p className="text-xs text-muted-foreground">Task Scheduler</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Scheduler Status */}
      <div className="p-4 border-t">
        <div className="flex items-center gap-2 mb-2">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Scheduler</span>
        </div>
        <div className="space-y-1 text-xs text-muted-foreground">
          <div className="flex items-center justify-between">
            <span>Status</span>
            <span className={cn(
              'flex items-center gap-1',
              status?.running ? 'text-success' : 'text-muted-foreground'
            )}>
              <span className={cn(
                'h-2 w-2 rounded-full',
                status?.running ? 'bg-success' : 'bg-muted-foreground'
              )} />
              {status?.running ? 'Running' : 'Stopped'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>Tasks</span>
            <span>{status?.enabled_tasks ?? 0} / {status?.total_tasks ?? 0}</span>
          </div>
          {status?.due_tasks !== undefined && status.due_tasks > 0 && (
            <div className="flex items-center justify-between text-primary">
              <span>Due now</span>
              <span>{status.due_tasks}</span>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}

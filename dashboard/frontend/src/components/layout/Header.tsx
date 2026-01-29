import { useLocation } from 'react-router-dom';

const pageTitles: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/tasks': 'Scheduled Tasks',
  '/skills': 'Skills',
  '/logs': 'Execution Logs',
};

export function Header() {
  const location = useLocation();

  // Get title, handling dynamic routes like /tasks/:id
  const getTitle = () => {
    const path = location.pathname;
    if (path.startsWith('/tasks/') && path !== '/tasks/') {
      return 'Task Details';
    }
    return pageTitles[path] || 'CodeGeass';
  };

  return (
    <header className="h-16 border-b bg-card px-6 flex items-center justify-between">
      <h1 className="text-xl font-serif font-semibold text-foreground">
        {getTitle()}
      </h1>
      <div className="flex items-center gap-4">
        {/* Future: Add refresh button, notifications, etc. */}
      </div>
    </header>
  );
}

# CodeGeass Dashboard - Frontend

React + TypeScript frontend for the CodeGeass Dashboard, built with Vite and styled with Tailwind CSS using the Claude Design System.

## Quick Start

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Production build
npm run build
```

Frontend available at http://localhost:5173

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS v4** - Utility-first styling
- **Zustand** - State management
- **React Router v6** - Client-side routing
- **Radix UI** - Accessible component primitives
- **Lucide React** - Icons

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx              # App entry point
│   ├── App.tsx               # Root component with routing
│   ├── index.css             # Global styles + Claude theme
│   │
│   ├── types/                # TypeScript interfaces
│   │   ├── index.ts          # Re-exports
│   │   ├── task.ts           # Task, TaskCreate, TaskUpdate
│   │   ├── skill.ts          # Skill, SkillSummary
│   │   ├── execution.ts      # ExecutionResult, LogStats
│   │   └── scheduler.ts      # SchedulerStatus, UpcomingRun
│   │
│   ├── lib/                  # Utilities
│   │   ├── api.ts            # API client (fetch wrapper)
│   │   └── utils.ts          # Helper functions
│   │
│   ├── stores/               # Zustand state stores
│   │   ├── index.ts          # Re-exports
│   │   ├── tasks.store.ts    # Task state + actions
│   │   ├── skills.store.ts   # Skill state + actions
│   │   ├── logs.store.ts     # Log state + filters
│   │   └── scheduler.store.ts # Scheduler status
│   │
│   ├── components/
│   │   ├── ui/               # Reusable UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Label.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Switch.tsx
│   │   │   ├── Textarea.tsx
│   │   │   ├── Dialog.tsx
│   │   │   ├── AlertDialog.tsx
│   │   │   ├── DropdownMenu.tsx
│   │   │   ├── Tabs.tsx
│   │   │   └── Toaster.tsx
│   │   │
│   │   ├── layout/           # Layout components
│   │   │   ├── Layout.tsx    # Main layout wrapper
│   │   │   ├── Sidebar.tsx   # Navigation sidebar
│   │   │   └── Header.tsx    # Page header
│   │   │
│   │   └── tasks/            # Task-specific components
│   │       ├── TaskCard.tsx  # Task card for grid
│   │       ├── TaskList.tsx  # Task grid with CRUD
│   │       └── TaskForm.tsx  # Create/edit form
│   │
│   └── pages/                # Route pages
│       ├── Dashboard.tsx     # Overview with stats
│       ├── Tasks.tsx         # Task management
│       ├── TaskDetail.tsx    # Single task view
│       ├── Skills.tsx        # Skill browser
│       └── Logs.tsx          # Execution history
│
├── index.html                # HTML template
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript config
├── package.json             # Dependencies
└── README.md                # This file
```

## Claude Design System

The dashboard implements the Claude visual design language:

### Colors

```css
/* Primary - Rust orange */
--color-primary: #C15F3C;
--color-primary-foreground: #ffffff;
--color-primary-hover: #A84E30;

/* Background - Off-white */
--color-background: #F4F3EE;
--color-foreground: #3d3929;

/* Cards */
--color-card: #ffffff;
--color-card-foreground: #3d3929;

/* Muted */
--color-muted: #E8E6DE;
--color-muted-foreground: #6b6455;

/* Status */
--color-destructive: #D64545;    /* Error */
--color-success: #22C55E;        /* Success */
--color-warning: #EAB308;        /* Warning */
```

### Typography

```css
/* Headers */
font-family: 'Georgia', serif;

/* Body text */
font-family: 'Inter', system-ui, sans-serif;

/* Code */
font-family: 'JetBrains Mono', monospace;
```

## Pages

### Dashboard (`/dashboard`)

Overview page with:
- Stats cards (total tasks, success rate, failures, due tasks)
- Upcoming runs list
- Recent executions list
- Quick action buttons

### Tasks (`/tasks`)

Task management grid:
- Task cards with status badges
- Enable/disable toggle
- Run, edit, delete actions
- Create new task dialog

### Task Detail (`/tasks/:taskId`)

Single task view with tabs:
- **Overview**: Stats, schedule info, execution details
- **Logs**: Execution history for this task
- **Config**: Raw JSON configuration

### Skills (`/skills`)

Skill browser:
- Grid of available skills
- Skill detail dialog with:
  - Description
  - Allowed tools
  - Dynamic commands
  - Content preview

### Logs (`/logs`)

Execution history:
- Stats cards
- Filter by status and task
- Expandable log entries with output

## State Management

### Zustand Stores

```typescript
// Task store
const { tasks, loading, fetchTasks, createTask } = useTasksStore();

// Skill store
const { skills, fetchSkills, reloadSkills } = useSkillsStore();

// Log store
const { logs, stats, fetchLogs, setStatusFilter } = useLogsStore();

// Scheduler store
const { status, upcoming, fetchStatus } = useSchedulerStore();
```

### Store Actions

#### Tasks Store

| Action | Description |
|--------|-------------|
| `fetchTasks()` | Load all tasks |
| `fetchTask(id)` | Load single task |
| `fetchTaskStats(id)` | Load task statistics |
| `createTask(data)` | Create new task |
| `updateTask(id, data)` | Update task |
| `deleteTask(id)` | Delete task |
| `enableTask(id)` | Enable task |
| `disableTask(id)` | Disable task |
| `runTask(id, dryRun?)` | Execute task |

#### Logs Store

| Action | Description |
|--------|-------------|
| `fetchLogs()` | Load logs with filters |
| `fetchTaskLogs(id, limit)` | Load logs for task |
| `fetchStats()` | Load statistics |
| `clearTaskLogs(id)` | Clear task logs |
| `setStatusFilter(status)` | Filter by status |
| `setTaskFilter(id)` | Filter by task |

## API Client

The API client in `lib/api.ts` provides typed fetch wrappers:

```typescript
import { api } from '@/lib/api';

// Tasks
const tasks = await api.tasks.list();
const task = await api.tasks.get(taskId);
await api.tasks.create({ name: 'test', schedule: '0 9 * * *', ... });
await api.tasks.run(taskId);

// Skills
const skills = await api.skills.list();
await api.skills.reload();

// Logs
const logs = await api.logs.list({ status: 'success', limit: 50 });
const stats = await api.logs.getStats();

// Scheduler
const status = await api.scheduler.getStatus();
const upcoming = await api.scheduler.getUpcoming(24);

// CRON validation
const result = await api.cron.validate('0 9 * * 1-5');
```

## Utility Functions

```typescript
import {
  cn,                    // Class name merger
  formatDate,            // Format ISO date to locale string
  formatRelativeTime,    // "2h ago", "in 5m"
  formatDuration,        // "45.2s", "2m 30s"
  getStatusColor,        // Status -> text color class
  getStatusBgColor,      // Status -> background color class
  getStatusIcon,         // Status -> emoji icon
} from '@/lib/utils';
```

## Components

### UI Components

Based on shadcn/ui patterns with Radix primitives:

```tsx
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Dialog, DialogContent, DialogHeader } from '@/components/ui/Dialog';
import { toast } from '@/components/ui/Toaster';

// Button variants
<Button>Default</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline">Cancel</Button>
<Button variant="ghost">Link</Button>
<Button variant="success">Success</Button>

// Badge variants
<Badge>Default</Badge>
<Badge variant="success">Success</Badge>
<Badge variant="destructive">Error</Badge>
<Badge variant="secondary">Disabled</Badge>

// Toast notifications
toast({ title: 'Task created', variant: 'success' });
toast({ title: 'Error', description: 'Details...', variant: 'destructive' });
```

### Task Components

```tsx
import { TaskCard } from '@/components/tasks/TaskCard';
import { TaskList } from '@/components/tasks/TaskList';
import { TaskForm } from '@/components/tasks/TaskForm';

// Task card
<TaskCard task={task} onDelete={() => handleDelete(task.id)} />

// Task form dialog
<TaskForm
  open={isOpen}
  onOpenChange={setIsOpen}
  onSubmit={handleCreate}
  initialData={task}  // For edit mode
  isEdit={true}
/>
```

## Routing

```tsx
// App.tsx
<Routes>
  <Route path="/" element={<Layout />}>
    <Route index element={<Navigate to="/dashboard" />} />
    <Route path="dashboard" element={<Dashboard />} />
    <Route path="tasks" element={<Tasks />} />
    <Route path="tasks/:taskId" element={<TaskDetail />} />
    <Route path="skills" element={<Skills />} />
    <Route path="logs" element={<Logs />} />
  </Route>
</Routes>
```

## Development

### Commands

```bash
npm run dev      # Start dev server (port 5173)
npm run build    # Production build
npm run lint     # ESLint check
npm run preview  # Preview production build
```

### Proxy Configuration

Development server proxies API requests to backend:

```typescript
// vite.config.ts
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:8001',
      changeOrigin: true,
    },
  },
}
```

### Adding New Components

1. Create component in appropriate directory
2. Add TypeScript interface if needed
3. Export from index if creating new directory
4. Follow existing patterns for styling

### Path Aliases

```typescript
// Use @ alias for src directory
import { Button } from '@/components/ui/Button';
import { useTasksStore } from '@/stores';
import type { Task } from '@/types';
```

## Building for Production

```bash
npm run build
```

Output in `dist/` directory:
- `index.html` - Entry HTML
- `assets/index-*.css` - Bundled CSS (~31KB gzipped: ~6KB)
- `assets/index-*.js` - Bundled JS (~387KB gzipped: ~117KB)

## Troubleshooting

### TypeScript errors on import
Ensure `@/*` path alias is configured in both `tsconfig.json` and `vite.config.ts`.

### API requests failing
Check that backend is running on port 8001 and Vite proxy is configured.

### Styles not applying
Ensure `index.css` is imported in `main.tsx` and Tailwind is configured.

### Toast not showing
Ensure `<Toaster />` is rendered in `App.tsx`.

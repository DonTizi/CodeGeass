import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { Tasks } from '@/pages/Tasks'
import { TaskDetail } from '@/pages/TaskDetail'
import { Skills } from '@/pages/Skills'
import { Logs } from '@/pages/Logs'
import { Settings } from '@/pages/Settings'
import { Projects } from '@/pages/Projects'
import { ApprovalDetail } from '@/pages/ApprovalDetail'
import { Toaster } from '@/components/ui/Toaster'
import { useExecutionWebSocket } from '@/hooks/useExecutionWebSocket'

function App() {
  // Initialize global WebSocket connection for execution monitoring
  useExecutionWebSocket({ enabled: true });

  return (
    <>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="tasks/:taskId" element={<TaskDetail />} />
          <Route path="approvals/:approvalId" element={<ApprovalDetail />} />
          <Route path="skills" element={<Skills />} />
          <Route path="logs" element={<Logs />} />
          <Route path="projects" element={<Projects />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
      <Toaster />
    </>
  )
}

export default App

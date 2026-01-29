import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { Tasks } from '@/pages/Tasks'
import { TaskDetail } from '@/pages/TaskDetail'
import { Skills } from '@/pages/Skills'
import { Logs } from '@/pages/Logs'
import { Toaster } from '@/components/ui/Toaster'

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="tasks/:taskId" element={<TaskDetail />} />
          <Route path="skills" element={<Skills />} />
          <Route path="logs" element={<Logs />} />
        </Route>
      </Routes>
      <Toaster />
    </>
  )
}

export default App

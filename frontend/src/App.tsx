import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { Spinner } from './components/ui'
import Landing from './screens/Landing'

// Lazy-load the heavier / 3D-bearing routes.
const Dashboard = lazy(() => import('./screens/Dashboard'))
const CyberRange = lazy(() => import('./screens/CyberRange'))
const Replay = lazy(() => import('./screens/Replay'))
const Arena = lazy(() => import('./screens/Arena'))
const ScenarioLibrary = lazy(() => import('./screens/ScenarioLibrary'))
const Reports = lazy(() => import('./screens/Reports'))

export default function App() {
  return (
    <AppShell>
      <Suspense fallback={<div className="grid min-h-[60vh] place-items-center"><Spinner /></div>}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/range" element={<CyberRange />} />
          <Route path="/replay" element={<Replay />} />
          <Route path="/arena" element={<Arena />} />
          <Route path="/scenarios" element={<ScenarioLibrary />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="*" element={<Landing />} />
        </Routes>
      </Suspense>
    </AppShell>
  )
}

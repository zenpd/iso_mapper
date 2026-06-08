import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { TransformPage } from './pages/TransformPage'
import { SamplesPage } from './pages/SamplesPage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import './index.css'

function App() {
  return (
    <Router>
      <AppShell>
        <Routes>
          <Route path="/" element={<TransformPage />} />
          <Route path="/samples" element={<SamplesPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>
    </Router>
  )
}

export default App

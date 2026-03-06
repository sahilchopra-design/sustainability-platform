import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import DataSources from './pages/DataSources'
import SourceDetail from './pages/SourceDetail'
import KpiFinder from './pages/KpiFinder'
import MappingStudio from './pages/MappingStudio'
import QueryBuilder from './pages/QueryBuilder'
import SyncMonitor from './pages/SyncMonitor'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="sources" element={<DataSources />} />
          <Route path="sources/:id" element={<SourceDetail />} />
          <Route path="kpis" element={<KpiFinder />} />
          <Route path="mappings" element={<MappingStudio />} />
          <Route path="query" element={<QueryBuilder />} />
          <Route path="sync" element={<SyncMonitor />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

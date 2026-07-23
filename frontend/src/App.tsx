import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import ChatPage from './pages/ChatPage';
import DashboardPage from './pages/DashboardPage';
import AccessRequestsPage from './pages/AccessRequestsPage';
import ApprovalsPage from './pages/ApprovalsPage';

export default function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <div className="flex items-center justify-center h-screen" style={{ background: 'var(--bg-primary)' }}>
            <div className="text-center">
              <h1 className="text-4xl font-black tracking-tight mb-4" style={{ color: 'var(--text-primary)' }}>
                AIOps
              </h1>
              <p className="text-base" style={{ color: 'var(--text-secondary)' }}>Login coming soon</p>
            </div>
          </div>
        }
      />
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/chat" replace />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="access" element={<AccessRequestsPage />} />
        <Route path="approvals" element={<ApprovalsPage />} />
      </Route>
    </Routes>
  );
}

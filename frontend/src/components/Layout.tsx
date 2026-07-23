import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function Layout() {
  return (
    <div className="flex h-screen" style={{ background: 'var(--bg-primary)' }}>
      <Sidebar />
      <main className="flex-1 overflow-hidden relative">
        <div className="absolute inset-0 overflow-y-auto" style={{ scrollBehavior: 'smooth' }}>
          <Outlet />
        </div>
      </main>
    </div>
  );
}

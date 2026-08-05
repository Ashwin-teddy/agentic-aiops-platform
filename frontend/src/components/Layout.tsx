import { Outlet } from 'react-router-dom';
import { Menu } from 'lucide-react';
import Sidebar from './Sidebar';
import { useAppStore } from '../store';

export default function Layout() {
  const toggleSidebar = useAppStore((s) => s.toggleSidebar);

  return (
    <div className="flex h-screen" style={{ background: 'var(--bg-primary)' }}>
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden relative">
        <button
          onClick={toggleSidebar}
          className="md:hidden fixed top-4 left-4 z-30 p-2.5 rounded-xl backdrop-blur-lg shadow-lg"
          style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}
        >
          <Menu className="w-5 h-5" style={{ color: 'var(--text-primary)' }} />
        </button>
        <div className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8" style={{ scrollBehavior: 'smooth' }}>
          <Outlet />
        </div>
      </main>
    </div>
  );
}

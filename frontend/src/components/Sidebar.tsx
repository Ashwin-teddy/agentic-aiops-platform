import { NavLink } from 'react-router-dom';
import { MessageSquare, LayoutDashboard, Shield, CheckSquare, Zap, X } from 'lucide-react';
import { useAppStore } from '../store';

const links = [
  { to: '/chat', icon: MessageSquare, label: 'Chat' },
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/access', icon: Shield, label: 'Access' },
  { to: '/approvals', icon: CheckSquare, label: 'Approvals' },
];

export default function Sidebar() {
  const sidebarOpen = useAppStore((s) => s.sidebarOpen);
  const toggleSidebar = useAppStore((s) => s.toggleSidebar);

  return (
    <>
      <div
        className={`fixed inset-0 bg-black/30 z-40 transition-opacity duration-300 md:hidden ${
          sidebarOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={toggleSidebar}
      />
      <aside
        className={`fixed md:relative z-50 w-[260px] flex flex-col border-r transition-transform duration-300 h-full ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
        style={{
          background: 'var(--bg-secondary)',
          borderColor: 'var(--border)',
        }}
      >
        <div className="flex items-center justify-between p-6 pb-4">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'var(--gradient-1)' }}
            >
              <Zap className="w-5 h-5 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <h1 className="text-lg font-extrabold tracking-tight" style={{ color: 'var(--text-primary)' }}>
                AIOps
              </h1>
              <p className="text-[11px] font-medium tracking-widest uppercase" style={{ color: 'var(--text-muted)' }}>
                Platform
              </p>
            </div>
          </div>
          <button
            onClick={toggleSidebar}
            className="md:hidden p-1 rounded-lg hover:bg-black/5 transition-colors"
          >
            <X className="w-5 h-5" style={{ color: 'var(--text-secondary)' }} />
          </button>
        </div>

        <div className="glow-line mx-6" />

        <nav className="flex-1 p-4 space-y-1">
          <p className="text-[10px] font-bold tracking-[0.2em] uppercase px-3 mb-3" style={{ color: 'var(--text-muted)' }}>
            Navigation
          </p>
          {links.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => {
                if (window.innerWidth < 768) toggleSidebar();
              }}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 ${
                  isActive ? 'scale-[1.02]' : ''
                }`
              }
              style={({ isActive }) => ({
                background: isActive ? 'rgba(0, 113, 227, 0.08)' : 'transparent',
                color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
                borderLeft: isActive ? '3px solid var(--accent)' : '3px solid transparent',
              })}
            >
              <Icon className="w-[18px] h-[18px]" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="p-4 space-y-3">
          <div className="glow-line" />
          <div
            className="p-4 rounded-xl text-center"
            style={{ background: 'rgba(0, 0, 0, 0.03)', border: '1px solid var(--border)' }}
          >
            <div className="w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center" style={{ background: 'var(--gradient-1)' }}>
              <span className="text-white text-xs font-bold">AI</span>
            </div>
            <p className="text-[11px] font-semibold" style={{ color: 'var(--text-primary)' }}>Enterprise v1.0</p>
            <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>AI-Powered IT Ops</p>
          </div>
        </div>
      </aside>
    </>
  );
}

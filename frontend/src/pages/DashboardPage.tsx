import { useQuery } from '@tanstack/react-query';
import { Activity, CheckCircle, AlertTriangle, Clock, Server, ArrowUpRight, Zap, TrendingUp } from 'lucide-react';
import { healthAPI } from '../services/api';

const stats = [
  { icon: Activity, label: 'System Status', key: 'status', fallback: 'Checking...', gradient: 'linear-gradient(135deg, #00d26a, #00a854)' },
  { icon: Server, label: 'Tools Active', key: 'tools', fallback: '0', gradient: 'var(--gradient-1)' },
  { icon: CheckCircle, label: 'Sessions', key: 'sessions', fallback: '0', gradient: 'linear-gradient(135deg, #6366f1, #8b5cf6)' },
  { icon: Clock, label: 'Avg Response', key: 'response', fallback: '< 2s', gradient: 'linear-gradient(135deg, #f59e0b, #f97316)' },
];

export default function DashboardPage() {
  const { data: tools } = useQuery({ queryKey: ['tools'], queryFn: () => healthAPI.tools().then((r) => r.data) });
  const { data: health } = useQuery({ queryKey: ['health'], queryFn: () => healthAPI.check().then((r) => r.data) });

  const getValue = (key: string) => {
    switch (key) {
      case 'status': return health?.status || 'Checking...';
      case 'tools': return String(tools?.length || 0);
      default: return stats.find((s) => s.key === key)?.fallback || '0';
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 sm:space-y-8 animate-fade-in" style={{ background: 'var(--bg-primary)' }}>
      {/* Hero Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold tracking-[0.3em] uppercase mb-2" style={{ color: 'var(--accent)' }}>
            Overview
          </p>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black tracking-tight" style={{ color: 'var(--text-primary)' }}>
            Dashboard
          </h1>
          <p className="text-sm sm:text-base mt-1 sm:mt-2" style={{ color: 'var(--text-secondary)' }}>
            Real-time system monitoring and tool health
          </p>
        </div>
        <div
          className="self-start sm:self-auto flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full"
          style={{ background: 'rgba(0, 210, 106, 0.1)', border: '1px solid rgba(0, 210, 106, 0.2)' }}
        >
          <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: 'var(--success)' }} />
          <span className="text-[10px] sm:text-xs font-bold" style={{ color: 'var(--success)' }}>ALL SYSTEMS OPERATIONAL</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {stats.map(({ icon: Icon, label, gradient }) => (
          <div key={label} className="glass-card p-4 sm:p-6 group cursor-default">
            <div className="flex items-center justify-between mb-4">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{ background: gradient }}
              >
                <Icon className="w-6 h-6 text-white" />
              </div>
              <ArrowUpRight
                className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-all duration-300 transform group-hover:-translate-y-0.5"
                style={{ color: 'var(--text-muted)' }}
              />
            </div>
            <p className="text-xs font-bold tracking-wider uppercase mb-1" style={{ color: 'var(--text-muted)' }}>
              {label}
            </p>
            <p className="text-xl sm:text-2xl lg:text-3xl font-black tracking-tight" style={{ color: 'var(--text-primary)' }}>
              {getValue(label === 'Tools Active' ? 'tools' : label === 'System Status' ? 'status' : label === 'Sessions' ? 'sessions' : 'response')}
            </p>
          </div>
        ))}
      </div>

      {/* Tool Health */}
      <div className="glass-card p-4 sm:p-6 lg:p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg sm:text-xl font-extrabold tracking-tight" style={{ color: 'var(--text-primary)' }}>
              Tool Health
            </h3>
            <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
              Registered enterprise integrations
            </p>
          </div>
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-full"
            style={{ background: 'rgba(0, 113, 227, 0.08)', border: '1px solid rgba(0, 113, 227, 0.2)' }}
          >
            <Zap className="w-3 h-3" style={{ color: 'var(--accent)' }} />
            <span className="text-xs font-bold" style={{ color: 'var(--accent)' }}>{tools?.length || 0} Active</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tools?.map((tool: { name: string; description: string }) => (
            <div
              key={tool.name}
              className="flex items-center gap-4 p-4 rounded-xl transition-all duration-300 group cursor-default"
              style={{ background: 'rgba(0, 0, 0, 0.03)', border: '1px solid var(--border)' }}
            >
              <div className="relative">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'var(--gradient-1)' }}>
                  <TrendingUp className="w-5 h-5 text-white" />
                </div>
                <div
                  className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2"
                  style={{ background: 'var(--success)', borderColor: 'var(--bg-primary)' }}
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-bold truncate" style={{ color: 'var(--text-primary)' }}>
                  {tool.name}
                </div>
                <div className="text-xs mt-0.5 truncate" style={{ color: 'var(--text-muted)' }}>
                  {tool.description}
                </div>
              </div>
            </div>
          ))}
          {(!tools || tools.length === 0) && (
            <div className="col-span-3 flex flex-col items-center justify-center py-16">
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
                style={{ background: 'rgba(255, 193, 7, 0.1)', border: '1px solid rgba(255, 193, 7, 0.2)' }}
              >
                <AlertTriangle className="w-8 h-8" style={{ color: 'var(--warning)' }} />
              </div>
              <p className="text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>
                No tools loaded
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                Check backend connectivity
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

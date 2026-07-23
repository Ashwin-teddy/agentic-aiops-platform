import { useQuery } from '@tanstack/react-query';
import { CheckSquare, Check, X, Clock, Shield } from 'lucide-react';
import { accessAPI } from '../services/api';
import type { Approval } from '../types';

const riskColor = (level: string) => {
  switch (level?.toLowerCase()) {
    case 'low': return { bg: 'rgba(0, 210, 106, 0.1)', border: 'rgba(0, 210, 106, 0.2)', text: 'var(--success)' };
    case 'medium': return { bg: 'rgba(255, 193, 7, 0.1)', border: 'rgba(255, 193, 7, 0.2)', text: 'var(--warning)' };
    case 'high': return { bg: 'rgba(255, 77, 0, 0.1)', border: 'rgba(255, 77, 0, 0.2)', text: 'var(--accent)' };
    case 'critical': return { bg: 'rgba(255, 59, 59, 0.1)', border: 'rgba(255, 59, 59, 0.2)', text: 'var(--error)' };
    default: return { bg: 'rgba(255, 255, 255, 0.05)', border: 'var(--border)', text: 'var(--text-secondary)' };
  }
};

export default function ApprovalsPage() {
  const { data: approvals, refetch } = useQuery({
    queryKey: ['approvals'],
    queryFn: () => accessAPI.getPending().then((r) => r.data),
  });

  const handleDecision = async (approvalId: string, decision: string) => {
    await accessAPI.approve(approvalId, decision, '');
    refetch();
  };

  return (
    <div className="p-8 max-w-5xl animate-fade-in" style={{ background: 'var(--bg-primary)' }}>
      {/* Header */}
      <div className="flex items-end justify-between mb-10">
        <div>
          <p className="text-xs font-bold tracking-[0.3em] uppercase mb-2" style={{ color: 'var(--accent)' }}>
            Approvals
          </p>
          <h1 className="text-4xl font-black tracking-tight" style={{ color: 'var(--text-primary)' }}>
            Pending Approvals
          </h1>
          <p className="text-base mt-2" style={{ color: 'var(--text-secondary)' }}>
            Review and act on access requests
          </p>
        </div>
        <div
          className="flex items-center gap-2 px-4 py-2 rounded-full"
          style={{ background: 'rgba(255, 193, 7, 0.1)', border: '1px solid rgba(255, 193, 7, 0.2)' }}
        >
          <Clock className="w-3.5 h-3.5" style={{ color: 'var(--warning)' }} />
          <span className="text-xs font-bold" style={{ color: 'var(--warning)' }}>
            {approvals?.length || 0} Pending
          </span>
        </div>
      </div>

      {/* Approvals List */}
      <div className="space-y-4">
        {(approvals as Approval[] | undefined)?.map((a, i) => {
          const rc = riskColor(a.risk_level);
          return (
            <div
              key={a.approval_id}
              className="glass-card p-6 animate-slide-up"
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <div className="flex items-start justify-between gap-6">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center"
                      style={{ background: 'var(--gradient-1)' }}
                    >
                      <Shield className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h4 className="text-base font-bold" style={{ color: 'var(--text-primary)' }}>
                        {a.resource_type} — {a.access_type}
                      </h4>
                      <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                        ID: {a.approval_id}
                      </p>
                    </div>
                  </div>
                  <p className="text-sm mb-3" style={{ color: 'var(--text-secondary)' }}>
                    {a.justification || 'No justification provided'}
                  </p>
                  <div className="flex items-center gap-3">
                    <span
                      className="px-3 py-1 rounded-full text-xs font-bold"
                      style={{ background: rc.bg, border: `1px solid ${rc.border}`, color: rc.text }}
                    >
                      {a.risk_level?.toUpperCase()} Risk
                    </span>
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                      Score: {a.risk_score?.toFixed(2)}
                    </span>
                  </div>
                </div>

                <div className="flex gap-2 shrink-0">
                  <button
                    onClick={() => handleDecision(a.approval_id, 'approved')}
                    className="flex items-center gap-1.5 px-5 py-2.5 rounded-full text-sm font-bold transition-all duration-300 hover:scale-105"
                    style={{
                      background: 'rgba(0, 210, 106, 0.15)',
                      color: 'var(--success)',
                      border: '1px solid rgba(0, 210, 106, 0.3)',
                    }}
                  >
                    <Check className="w-4 h-4" />
                    Approve
                  </button>
                  <button
                    onClick={() => handleDecision(a.approval_id, 'rejected')}
                    className="flex items-center gap-1.5 px-5 py-2.5 rounded-full text-sm font-bold transition-all duration-300 hover:scale-105"
                    style={{
                      background: 'rgba(255, 59, 59, 0.15)',
                      color: 'var(--error)',
                      border: '1px solid rgba(255, 59, 59, 0.3)',
                    }}
                  >
                    <X className="w-4 h-4" />
                    Reject
                  </button>
                </div>
              </div>
            </div>
          );
        })}

        {(!approvals || approvals.length === 0) && (
          <div className="glass-card flex flex-col items-center justify-center py-20">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
              style={{ background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border)' }}
            >
              <CheckSquare className="w-8 h-8" style={{ color: 'var(--text-muted)' }} />
            </div>
            <p className="text-lg font-bold" style={{ color: 'var(--text-secondary)' }}>
              All clear
            </p>
            <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
              No pending approvals
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

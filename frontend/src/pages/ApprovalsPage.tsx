import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { CheckSquare, Check, X, Clock, Shield, Share2 } from 'lucide-react';
import { accessAPI } from '../services/api';
import type { Approval } from '../types';

const riskColor = (level: string) => {
  switch (level?.toLowerCase()) {
    case 'low': return { bg: 'rgba(0, 210, 106, 0.1)', border: 'rgba(0, 210, 106, 0.2)', text: 'var(--success)' };
    case 'medium': return { bg: 'rgba(255, 193, 7, 0.1)', border: 'rgba(255, 193, 7, 0.2)', text: 'var(--warning)' };
    case 'high': return { bg: 'rgba(255, 149, 0, 0.12)', border: 'rgba(255, 149, 0, 0.3)', text: '#ff9500' };
    case 'critical': return { bg: 'rgba(255, 59, 59, 0.1)', border: 'rgba(255, 59, 59, 0.2)', text: 'var(--error)' };
    default: return { bg: 'rgba(0, 0, 0, 0.04)', border: 'var(--border)', text: 'var(--text-secondary)' };
  }
};

const resourceLabels: Record<string, string> = {
  jira: 'Jira',
  confluence: 'Confluence',
  google_drive: 'Google Drive',
  github: 'GitHub',
  aws_iam: 'AWS IAM',
  kubernetes: 'Kubernetes',
  azure_ad: 'Azure AD',
  okta: 'Okta',
  servicenow: 'ServiceNow',
};

export default function ApprovalsPage() {
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [removedIds, setRemovedIds] = useState<Set<string>>(new Set());
  const { data: approvals, refetch } = useQuery({
    queryKey: ['approvals'],
    queryFn: () => accessAPI.getPending().then((r) => r.data),
  });

  const pendingList = ((approvals as Approval[] | undefined) ?? []).filter((a) => !removedIds.has(a.approval_id));

  const handleDecision = async (approvalId: string, decision: string) => {
    try {
      const { data } = await accessAPI.approve(approvalId, decision, '');
      const shares: Array<{ success: boolean; message?: string; error?: string }> = data?.share_results;
      if (decision === 'approved') {
        if (shares && shares.length > 0) {
          const failed = shares.filter((s) => !s.success);
          if (failed.length === 0) {
            setFeedback({
              type: 'success',
              message: `Approved — granted access to ${shares.length} recipient${shares.length > 1 ? 's' : ''}.`,
            });
          } else {
            setFeedback({
              type: 'error',
              message: `Approved, but failed for ${failed.length} recipient${failed.length > 1 ? 's' : ''}: ${failed[0]?.error}`,
            });
          }
        } else {
          setFeedback({ type: 'success', message: 'Approved' });
        }
      } else {
        setFeedback({ type: 'success', message: 'Rejected' });
      }
      setRemovedIds((prev) => new Set(prev).add(approvalId));
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFeedback({ type: 'error', message: detail || 'Failed to record decision.' });
    }
    refetch();
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-5xl animate-fade-in" style={{ background: 'var(--bg-primary)' }}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6 sm:mb-10">
        <div>
          <p className="text-xs font-bold tracking-[0.3em] uppercase mb-2" style={{ color: 'var(--accent)' }}>
            Approvals
          </p>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black tracking-tight" style={{ color: 'var(--text-primary)' }}>
            Pending Approvals
          </h1>
          <p className="text-sm sm:text-base mt-1 sm:mt-2" style={{ color: 'var(--text-secondary)' }}>
            Review and act on access requests
          </p>
        </div>
        <div
          className="self-start sm:self-auto flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full"
          style={{ background: 'rgba(255, 193, 7, 0.1)', border: '1px solid rgba(255, 193, 7, 0.2)' }}
        >
          <Clock className="w-3.5 h-3.5" style={{ color: 'var(--warning)' }} />
          <span className="text-xs font-bold" style={{ color: 'var(--warning)' }}>
            {pendingList.length} Pending
          </span>
        </div>
      </div>

      {/* Approvals List */}
      <div className="space-y-4">
        {pendingList.map((a, i) => {
          const rc = riskColor(a.risk_level);
          return (
            <div
              key={a.approval_id}
              className="glass-card p-4 sm:p-6 animate-slide-up"
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 sm:gap-6">
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
                        {resourceLabels[a.resource_type] || a.resource_type} — {a.access_type}
                      </h4>
                      <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                        ID: {a.approval_id}
                      </p>
                    </div>
                  </div>
                  <p className="text-sm mb-3" style={{ color: 'var(--text-secondary)' }}>
                    {a.justification || 'No justification provided'}
                  </p>
                  {a.resource_identifier && (
                    <p className="text-xs mb-3 flex items-center gap-1.5 font-mono" style={{ color: 'var(--text-muted)' }}>
                      <Share2 className="w-3.5 h-3.5" />
                      {a.resource_identifier}
                      {' → '}
                      {(a.share_with_emails?.length ? a.share_with_emails : a.requester_email ? [a.requester_email] : []).join(', ')}
                    </p>
                  )}
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

                <div className="flex gap-2 sm:shrink-0">
                  <button
                    onClick={() => handleDecision(a.approval_id, 'approved')}
                    className="flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-4 sm:px-5 py-2.5 rounded-full text-sm font-bold transition-all duration-300 hover:scale-105"
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
                    className="flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-4 sm:px-5 py-2.5 rounded-full text-sm font-bold transition-all duration-300 hover:scale-105"
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

        {pendingList.length === 0 && (
          <div className="glass-card flex flex-col items-center justify-center py-20">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
              style={{ background: 'rgba(0, 0, 0, 0.03)', border: '1px solid var(--border)' }}
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

      {feedback && (
        <div
          className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-start gap-3 px-5 py-4 rounded-2xl shadow-2xl animate-slide-up"
          style={{
            background: feedback.type === 'success' ? 'rgba(0, 210, 106, 0.12)' : 'rgba(255, 59, 59, 0.12)',
            border: `1px solid ${feedback.type === 'success' ? 'rgba(0, 210, 106, 0.3)' : 'rgba(255, 59, 59, 0.3)'}`,
            backdropFilter: 'blur(12px)',
          }}
        >
          {feedback.type === 'success' ? (
            <Check className="w-5 h-5 mt-0.5 shrink-0" style={{ color: 'var(--success)' }} />
          ) : (
            <X className="w-5 h-5 mt-0.5 shrink-0" style={{ color: 'var(--error)' }} />
          )}
          <p className="text-sm font-semibold max-w-md" style={{ color: 'var(--text-primary)' }}>
            {feedback.message}
          </p>
          <button
            onClick={() => setFeedback(null)}
            className="ml-2 text-xs font-bold hover:opacity-70"
            style={{ color: 'var(--text-muted)' }}
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}

import { useState } from 'react';
import { Shield, Send, CheckCircle, AlertCircle } from 'lucide-react';
import { accessAPI } from '../services/api';

export default function AccessRequestsPage() {
  const [resourceType, setResourceType] = useState('jira');
  const [resourceId, setResourceId] = useState('');
  const [accessType, setAccessType] = useState('read');
  const [justification, setJustification] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const handleSubmit = async () => {
    if (!resourceId || !justification) return;
    setSubmitting(true);
    try {
      const { data } = await accessAPI.createRequest({
        resource_type: resourceType,
        resource_identifier: resourceId,
        access_type: accessType,
        justification,
      });
      setResult({ type: 'success', message: `Request ${data.request_id} — ${data.status} (Risk: ${data.risk_level})` });
    } catch {
      setResult({ type: 'error', message: 'Failed to submit request. Please try again.' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-3xl animate-fade-in" style={{ background: 'var(--bg-primary)' }}>
      {/* Header */}
      <div className="mb-6 sm:mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div
            className="w-10 sm:w-12 h-10 sm:h-12 rounded-xl flex items-center justify-center"
            style={{ background: 'var(--gradient-1)' }}
          >
            <Shield className="w-5 sm:w-6 h-5 sm:h-6 text-white" />
          </div>
          <div>
            <p className="text-xs font-bold tracking-[0.3em] uppercase" style={{ color: 'var(--accent)' }}>
              Request
            </p>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight" style={{ color: 'var(--text-primary)' }}>
              Access Request
            </h1>
          </div>
        </div>
        <p className="text-sm sm:text-base" style={{ color: 'var(--text-secondary)' }}>
          Request access to enterprise tools and resources with AI-powered risk assessment.
        </p>
      </div>

      {/* Form */}
      <div className="glass-card p-4 sm:p-6 lg:p-8 space-y-5 sm:space-y-6">
        {/* Row 1 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5">
          <div>
            <label className="block text-xs font-bold tracking-wider uppercase mb-2" style={{ color: 'var(--text-muted)' }}>
              Resource Type
            </label>
            <select
              value={resourceType}
              onChange={(e) => setResourceType(e.target.value)}
              className="select-field"
            >
              <option value="jira">Jira</option>
              <option value="confluence">Confluence</option>
              <option value="google_drive">Google Drive</option>
              <option value="github">GitHub</option>
              <option value="aws_iam">AWS IAM</option>
              <option value="kubernetes">Kubernetes</option>
              <option value="azure_ad">Azure AD</option>
              <option value="okta">Okta</option>
              <option value="servicenow">ServiceNow</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-bold tracking-wider uppercase mb-2" style={{ color: 'var(--text-muted)' }}>
              Access Level
            </label>
            <select
              value={accessType}
              onChange={(e) => setAccessType(e.target.value)}
              className="select-field"
            >
              <option value="read">Read</option>
              <option value="write">Write</option>
              <option value="admin">Admin</option>
            </select>
          </div>
        </div>

        {/* Resource ID */}
        <div>
          <label className="block text-xs font-bold tracking-wider uppercase mb-2" style={{ color: 'var(--text-muted)' }}>
            Resource Identifier
          </label>
          <input
            type="text"
            value={resourceId}
            onChange={(e) => setResourceId(e.target.value)}
            placeholder="e.g., PROJECT-123, my-repo, prod-cluster"
            className="input-field"
          />
        </div>

        {/* Justification */}
        <div>
          <label className="block text-xs font-bold tracking-wider uppercase mb-2" style={{ color: 'var(--text-muted)' }}>
            Business Justification
          </label>
          <textarea
            value={justification}
            onChange={(e) => setJustification(e.target.value)}
            rows={4}
            placeholder="Explain why you need this access..."
            className="input-field resize-none"
          />
        </div>

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={submitting || !resourceId || !justification}
          className="btn-primary w-full flex items-center justify-center gap-2 text-base"
        >
          {submitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Submitting...
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              Submit Request
            </>
          )}
        </button>

        {/* Result */}
        {result && (
          <div
            className="flex items-start gap-3 p-4 rounded-xl animate-slide-up"
            style={{
              background: result.type === 'success' ? 'rgba(0, 210, 106, 0.08)' : 'rgba(255, 59, 59, 0.08)',
              border: `1px solid ${result.type === 'success' ? 'rgba(0, 210, 106, 0.2)' : 'rgba(255, 59, 59, 0.2)'}`,
            }}
          >
            {result.type === 'success' ? (
              <CheckCircle className="w-5 h-5 mt-0.5 shrink-0" style={{ color: 'var(--success)' }} />
            ) : (
              <AlertCircle className="w-5 h-5 mt-0.5 shrink-0" style={{ color: 'var(--error)' }} />
            )}
            <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
              {result.message}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

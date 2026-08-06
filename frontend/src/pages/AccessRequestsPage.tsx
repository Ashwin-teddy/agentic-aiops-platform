import { useState, useEffect } from 'react';
import { Shield, Send, CheckCircle, AlertCircle, FolderOpen, Link2, PlugZap, Loader2 } from 'lucide-react';
import { accessAPI, driveAPI } from '../services/api';

export default function AccessRequestsPage() {
  const [resourceType, setResourceType] = useState('jira');
  const [resourceId, setResourceId] = useState('');
  const [accessType, setAccessType] = useState('read');
  const [justification, setJustification] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const [driveConnected, setDriveConnected] = useState(false);
  const [driveEmail, setDriveEmail] = useState('');
  const [driveLoading, setDriveLoading] = useState(true);
  const [driveAuthUrl, setDriveAuthUrl] = useState('');

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const { data } = await driveAPI.getAuthUrl();
        if (!mounted) return;
        setDriveConnected(data.connected);
        setDriveEmail(data.email || '');
        setDriveAuthUrl(data.auth_url || '');
      } catch {
        if (!mounted) return;
        setDriveConnected(false);
      } finally {
        if (mounted) setDriveLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const isDrive = resourceType === 'google_drive';

  const handleConnect = () => {
    if (driveAuthUrl) window.location.href = driveAuthUrl;
  };

  const handleDisconnect = async () => {
    setDriveLoading(true);
    try {
      await driveAPI.disconnect();
      setDriveConnected(false);
      setDriveEmail('');
    } catch {
      setResult({ type: 'error', message: 'Failed to disconnect Google Drive.' });
    } finally {
      setDriveLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!resourceId || !justification) return;
    if (isDrive && !driveConnected) {
      setResult({ type: 'error', message: 'Connect Google Drive first so the approver can share the folder with you.' });
      return;
    }
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

      {/* Google Drive connection */}
      {isDrive && (
        <div className="glass-card p-4 sm:p-6 mb-6 animate-slide-up">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                style={{ background: 'var(--gradient-1)' }}
              >
                <FolderOpen className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
                  Google Drive Connection
                </p>
                <p className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>
                  {driveLoading
                    ? 'Checking connection...'
                    : driveConnected
                      ? `Connected as ${driveEmail}`
                      : 'Connect your Google account so folders can be shared with you'}
                </p>
              </div>
            </div>
            {!driveLoading && driveConnected && (
              <span
                className="self-start sm:self-auto flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold"
                style={{ background: 'rgba(0, 210, 106, 0.12)', border: '1px solid rgba(0, 210, 106, 0.25)', color: 'var(--success)' }}
              >
                <CheckCircle className="w-3.5 h-3.5" />
                Connected
              </span>
            )}
            {!driveLoading && (
              <button
                onClick={driveConnected ? handleDisconnect : handleConnect}
                disabled={!driveAuthUrl && !driveConnected}
                className="self-start sm:self-auto flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold transition-all duration-300 hover:scale-105"
                style={
                  driveConnected
                    ? { background: 'rgba(255, 59, 59, 0.1)', color: 'var(--error)', border: '1px solid rgba(255, 59, 59, 0.25)' }
                    : { background: 'var(--accent)', color: '#fff' }
                }
              >
                {driveLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : driveConnected ? <PlugZap className="w-4 h-4" /> : <Link2 className="w-4 h-4" />}
                {driveConnected ? 'Disconnect' : 'Connect Google Drive'}
              </button>
            )}
          </div>
        </div>
      )}

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
            placeholder={
              isDrive
                ? 'Google Drive folder/file link or ID (e.g., https://drive.google.com/drive/folders/abc123)'
                : 'e.g., PROJECT-123, my-repo, prod-cluster'
            }
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

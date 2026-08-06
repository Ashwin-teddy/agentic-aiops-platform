export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  intent?: string;
  citations?: Citation[];
  status?: string;
}

export interface Citation {
  index: number;
  title: string;
  source: string;
  source_url: string;
  score: number;
}

export interface Session {
  id: string;
  userId: string;
  createdAt: string;
  status: 'active' | 'closed';
}

export interface AccessRequest {
  request_id: string;
  user_id: string;
  resource_type: string;
  resource_identifier: string;
  access_type: string;
  risk_level: string;
  risk_score: number;
  status: string;
  justification: string;
  created_at: string;
}

export interface Approval {
  approval_id: string;
  request_id: string;
  requester_id: string;
  requester_email?: string;
  resource_type: string;
  resource_identifier?: string;
  access_type: string;
  risk_level: string;
  risk_score: number;
  status: string;
  justification: string;
  created_at: string;
}

export interface ToolStatus {
  name: string;
  healthy: boolean;
  latency?: number;
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: string;
  permissions: string[];
}

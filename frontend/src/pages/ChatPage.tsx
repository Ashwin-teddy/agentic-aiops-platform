import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, ExternalLink, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { chatAPI } from '../services/api';
import { useAppStore } from '../store';
import type { ChatMessage } from '../types';

const quickActions = [
  { label: 'Check service health', icon: '⚡' },
  { label: 'Request Jira access', icon: '🔑' },
  { label: 'Troubleshoot API errors', icon: '🔧' },
  { label: 'Search runbooks', icon: '📚' },
];

export default function ChatPage() {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, addMessage, sessionId, setSessionId, isLoading, setIsLoading } = useAppStore();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };
    addMessage(userMsg);
    setInput('');
    setIsLoading(true);
    try {
      const { data } = await chatAPI.sendMessage(input, sessionId || undefined);
      if (data.session_id && !sessionId) setSessionId(data.session_id);
      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        intent: data.intent,
        citations: data.citations,
        status: data.status,
      });
    } catch {
      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full" style={{ background: 'var(--bg-primary)' }}>
      {/* Header */}
      <header
        className="px-8 py-5 border-b flex items-center justify-between"
        style={{ borderColor: 'var(--border)', background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(20px)' }}
      >
        <div>
          <h2 className="text-xl font-extrabold tracking-tight" style={{ color: 'var(--text-primary)' }}>
            IT Operations Assistant
          </h2>
          <p className="text-sm mt-0.5" style={{ color: 'var(--text-secondary)' }}>
            Ask anything about incidents, access, or troubleshooting
          </p>
        </div>
        <div
          className="flex items-center gap-2 px-4 py-2 rounded-full"
          style={{ background: 'rgba(0, 210, 106, 0.1)', border: '1px solid rgba(0, 210, 106, 0.2)' }}
        >
          <div className="w-2 h-2 rounded-full" style={{ background: 'var(--success)' }} />
          <span className="text-xs font-semibold" style={{ color: 'var(--success)' }}>Online</span>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full animate-fade-in">
            <div
              className="w-20 h-20 rounded-2xl flex items-center justify-center mb-6"
              style={{ background: 'var(--gradient-1)', animation: 'pulse-glow 3s infinite' }}
            >
              <Sparkles className="w-10 h-10 text-white" />
            </div>
            <h3
              className="text-3xl font-extrabold tracking-tight mb-2"
              style={{ color: 'var(--text-primary)' }}
            >
              How can I help you?
            </h3>
            <p className="text-base max-w-md text-center" style={{ color: 'var(--text-secondary)' }}>
              Troubleshoot issues, request access, search runbooks, or check incident status — all powered by AI.
            </p>
            <div className="grid grid-cols-2 gap-3 mt-8 w-full max-w-lg">
              {quickActions.map((q) => (
                <button
                  key={q.label}
                  onClick={() => setInput(q.label)}
                  className="glass-card px-5 py-4 text-left group cursor-pointer"
                >
                  <span className="text-lg mb-2 block">{q.icon}</span>
                  <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                    {q.label}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-4 mb-6 animate-slide-up ${msg.role === 'user' ? 'justify-end' : ''}`}
          >
            {msg.role === 'assistant' && (
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                style={{ background: 'var(--gradient-1)' }}
              >
                <Bot className="w-5 h-5 text-white" />
              </div>
            )}
            <div
              className={`max-w-[70%] rounded-2xl px-5 py-4 ${
                msg.role === 'user' ? 'rounded-br-md' : 'rounded-bl-md'
              }`}
              style={{
                background: msg.role === 'user' ? 'var(--accent)' : 'var(--bg-card)',
                color: msg.role === 'user' ? '#fff' : 'var(--text-primary)',
                border: msg.role === 'user' ? 'none' : '1px solid var(--border)',
              }}
            >
              {msg.intent && (
                <div className="text-xs font-semibold mb-2 flex items-center gap-1.5" style={{ color: 'var(--accent-hover)' }}>
                  <Sparkles className="w-3 h-3" />
                  Intent: {msg.intent}
                </div>
              )}
              <div className="prose prose-invert prose-sm max-w-none" style={{ color: msg.role === 'user' ? '#fff' : 'var(--text-primary)' }}>
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
                  <p className="text-xs font-semibold mb-1.5" style={{ color: 'var(--text-muted)' }}>Sources</p>
                  {msg.citations.map((c) => (
                    <div key={c.index} className="flex items-center gap-1.5 text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>
                      <ExternalLink className="w-3 h-3" />
                      <span>[{c.index}] {c.title} ({c.source})</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                style={{ background: 'var(--bg-elevated)' }}
              >
                <User className="w-5 h-5" style={{ color: 'var(--text-secondary)' }} />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-4 mb-6 animate-fade-in">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: 'var(--gradient-1)' }}
            >
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div
              className="rounded-2xl rounded-bl-md px-5 py-4 flex items-center gap-3"
              style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
            >
              <Loader2 className="w-4 h-4 animate-spin" style={{ color: 'var(--accent)' }} />
              <span className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-8 py-5 border-t" style={{ borderColor: 'var(--border)', background: 'rgba(0,0,0,0.3)' }}>
        <div className="flex gap-3 items-center max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Ask anything..."
              className="input-field pr-12"
              disabled={isLoading}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="btn-primary flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

import React, { useEffect, useState, useRef } from 'react';
import { tutorApi } from '../api';
import { ChatSession, ChatSessionSummary, ChatMessage } from '../api/types';
import { useAuth } from '../context/AuthContext';
import { Badge } from '../components/Badge';
import {
  Bot,
  Send,
  Sparkles,
  HelpCircle,
  Lightbulb,
  MessageSquare,
  PlusCircle,
  Brain
} from 'lucide-react';

export const AITutor: React.FC = () => {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const list = await tutorApi.getSessions();
        setSessions(list);
        if (list.length > 0) {
          const detail = await tutorApi.getSessionDetail(list[0].id);
          setActiveSession(detail);
        } else {
          // Create initial session
          const newSession = await tutorApi.createSession({ title: 'Python Loops & Iteration Tutoring' });
          setActiveSession(newSession);
          setSessions([{
            id: newSession.id,
            topic_id: newSession.topic_id,
            title: newSession.title,
            is_active: newSession.is_active,
            created_at: newSession.created_at,
            updated_at: newSession.updated_at,
            message_count: newSession.messages.length,
          }]);
        }
      } catch (err) {
        console.error('Failed to load tutor sessions:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSessions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [activeSession?.messages]);

  const handleSelectSession = async (sessionId: number) => {
    try {
      setLoading(true);
      const detail = await tutorApi.getSessionDetail(sessionId);
      setActiveSession(detail);
    } catch (err) {
      console.error('Failed to load session:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async () => {
    try {
      const newSession = await tutorApi.createSession({ title: `Tutoring Session #${sessions.length + 1}` });
      setActiveSession(newSession);
      setSessions((prev) => [
        {
          id: newSession.id,
          topic_id: newSession.topic_id,
          title: newSession.title,
          is_active: newSession.is_active,
          created_at: newSession.created_at,
          updated_at: newSession.updated_at,
          message_count: newSession.messages.length,
        },
        ...prev,
      ]);
    } catch (err) {
      console.error('Failed creating session:', err);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = textToSend || inputMessage;
    if (!query.trim() || sending) return;

    const currentSessionId = activeSession?.id;
    setInputMessage('');
    setSending(true);

    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: Date.now(),
      session_id: currentSessionId || 0,
      role: 'user',
      content: query,
      metadata_json: {},
      created_at: new Date().toISOString(),
    };

    setActiveSession((prev) => (prev ? { ...prev, messages: [...prev.messages, tempUserMsg] } : null));

    try {
      const response = await tutorApi.askTutor({
        session_id: currentSessionId,
        message: query,
      });

      const assistantMsg: ChatMessage = {
        id: Date.now() + 1,
        session_id: response.session_id,
        role: 'assistant',
        content: response.reply,
        metadata_json: {
          hints: response.hints,
          follow_up_questions: response.follow_up_questions,
        },
        created_at: new Date().toISOString(),
      };

      setActiveSession((prev) => (prev ? { ...prev, messages: [...prev.messages, assistantMsg] } : null));
    } catch (err) {
      console.error('Failed to get tutor reply:', err);
    } finally {
      setSending(false);
    }
  };

  if (loading && !activeSession) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col md:flex-row gap-6">
      {/* Sessions Sidebar */}
      <div className="w-full md:w-64 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono">
            Conversations
          </span>
          <button
            onClick={handleCreateSession}
            className="p-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-400 transition"
            title="Start New Session"
          >
            <PlusCircle className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map((sess) => (
            <button
              key={sess.id}
              onClick={() => handleSelectSession(sess.id)}
              className={`w-full text-left p-3 rounded-xl text-xs transition flex items-center gap-2.5 ${
                activeSession?.id === sess.id
                  ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <MessageSquare className="w-4 h-4 shrink-0 text-slate-500" />
              <span className="truncate font-medium">{sess.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Pane */}
      <div className="flex-1 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden">
        {/* Context Banner */}
        <div className="p-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-tight">
                {activeSession?.title || 'AI Tutor'}
              </h2>
              <p className="text-[11px] text-slate-400">
                Cognitive injection active: Adapts explanations to your current mastery
              </p>
            </div>
          </div>
          <Badge variant="indigo">Socratic Engine</Badge>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {activeSession?.messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0 mt-1">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-xl rounded-2xl p-4 text-xs leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white rounded-br-none shadow-md'
                    : 'bg-slate-950 border border-slate-800/90 text-slate-200 rounded-bl-none shadow-sm'
                }`}
              >
                <div className="whitespace-pre-line font-sans">{msg.content}</div>

                {/* Socratic Hints if present */}
                {msg.metadata_json?.hints && msg.metadata_json.hints.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-800 space-y-1.5">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-amber-400 font-semibold flex items-center gap-1">
                      <Lightbulb className="w-3 h-3" /> Conceptual Hints:
                    </span>
                    {msg.metadata_json.hints.map((hint: string, hIdx: number) => (
                      <p key={hIdx} className="text-[11px] text-slate-300 italic">
                        • {hint}
                      </p>
                    ))}
                  </div>
                )}

                {/* Follow up suggestions */}
                {msg.metadata_json?.follow_up_questions && msg.metadata_json.follow_up_questions.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-slate-800 space-y-1.5">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400 font-semibold flex items-center gap-1">
                      <HelpCircle className="w-3 h-3" /> Check Understanding:
                    </span>
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {msg.metadata_json.follow_up_questions.map((q: string, qIdx: number) => (
                        <button
                          key={qIdx}
                          onClick={() => handleSendMessage(q)}
                          className="text-[10px] bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1 text-slate-300 transition text-left"
                        >
                          "{q}"
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {sending && (
            <div className="flex gap-3 justify-start items-center text-xs text-slate-400">
              <div className="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
                <Bot className="w-4 h-4 animate-pulse" />
              </div>
              <div className="bg-slate-950 border border-slate-800 rounded-2xl px-4 py-3 text-slate-400">
                AI Tutor is analyzing your concept mastery and preparing an explanation...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Prompt Input Box */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-3"
          >
            <input
              type="text"
              placeholder="Ask a conceptual question (e.g. 'Why did my nested loop run 6 times?')..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              disabled={sending}
              className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
            <button
              type="submit"
              disabled={!inputMessage.trim() || sending}
              className="px-4 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition disabled:opacity-40 shadow-md shadow-indigo-600/20"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

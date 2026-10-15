'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Send, RotateCcw, Copy, ChevronDown, ChevronRight,
  AlertTriangle, BookOpen, Loader2, MessageSquare, Zap,
  CheckCircle, AlertOctagon, FileText, Hash,
} from 'lucide-react'
import type { ChatMessage, SourceCitation } from '@/types'
import { sendChat } from '@/lib/api'
import { generateId, cn } from '@/lib/utils'
import toast from 'react-hot-toast'

const SUGGESTED_QUESTIONS = [
  'When are the end-semester exams scheduled?',
  'What is the tuition fee for B.Tech?',
  'What documents do I need for registration?',
  'How do I download my admit card?',
  'What is the late fee for delayed payment?',
  'What is the minimum attendance required?',
]

// ── Typing indicator ─────────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 animate-fade-in">
      <div className="w-8 h-8 rounded-full bg-teal-500/20 border border-teal-500/30 
                      flex items-center justify-center shrink-0">
        <Zap className="w-4 h-4 text-teal-400" />
      </div>
      <div className="chat-bubble-assistant">
        <div className="flex gap-1 items-center py-1">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="text-xs text-slate-500 ml-2">Retrieving and generating…</span>
        </div>
      </div>
    </div>
  )
}

// ── Source citation panel ─────────────────────────────────────────────────────
function CitationPanel({ citations }: { citations: SourceCitation[] }) {
  const [open, setOpen] = useState(false)
  if (citations.length === 0) return null
  return (
    <div className="mt-3 border border-slate-700/50 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-2 
                   bg-slate-800/50 hover:bg-slate-800 transition-colors text-sm"
      >
        <div className="flex items-center gap-2 text-teal-400 font-medium">
          <BookOpen className="w-4 h-4" />
          Sources &amp; Evidence ({citations.length})
        </div>
        {open ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
      </button>

      {open && (
        <div className="divide-y divide-slate-700/30">
          {citations.map((c) => (
            <div key={c.source_id} className="px-4 py-3 bg-slate-900/40">
              <div className="flex items-start gap-2 mb-2">
                <span className="source-badge shrink-0">[{c.source_id}]</span>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="text-slate-300 text-xs font-medium truncate">{c.filename}</span>
                    {c.page && (
                      <span className="flex items-center gap-1 text-slate-500 text-xs">
                        <Hash className="w-3 h-3" /> Page {c.page}
                      </span>
                    )}
                    <span className="text-slate-600 text-xs ml-auto">
                      score: {(c.relevance_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
              <p className="text-slate-400 text-xs leading-relaxed pl-6 italic border-l-2 border-slate-700">
                &ldquo;{c.excerpt}&rdquo;
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Single chat message ───────────────────────────────────────────────────────
function ChatBubble({ msg, onRetry }: { msg: ChatMessage; onRetry?: () => void }) {
  const isUser = msg.role === 'user'

  const copyToClipboard = () => {
    navigator.clipboard.writeText(msg.content).then(() => {
      toast.success('Copied to clipboard')
    })
  }

  return (
    <div className={cn('flex items-start gap-3 animate-slide-up', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div className={cn(
        'w-8 h-8 rounded-full flex items-center justify-center shrink-0',
        isUser
          ? 'bg-teal-600/20 border border-teal-500/30'
          : 'bg-slate-700/50 border border-slate-600/50',
      )}>
        {isUser
          ? <MessageSquare className="w-4 h-4 text-teal-400" />
          : <Zap className="w-4 h-4 text-teal-400" />}
      </div>

      <div className={cn('max-w-[80%] space-y-2', isUser && 'items-end')}>
        {/* Bubble */}
        <div className={isUser ? 'chat-bubble-user' : 'chat-bubble-assistant'}>
          {isUser ? (
            <p className="text-sm">{msg.content}</p>
          ) : (
            <>
              {/* Abstention panel */}
              {msg.abstained && (
                <div className="abstention-panel mb-3">
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-amber-300 text-xs font-semibold mb-1">Could Not Verify</p>
                    <p className="text-amber-200/70 text-xs">{msg.abstention_reason}</p>
                  </div>
                </div>
              )}

              {/* Conflict panel */}
              {msg.conflict_detected && (
                <div className="conflict-panel mb-3">
                  <AlertOctagon className="w-4 h-4 text-orange-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-orange-300 text-xs font-semibold mb-1">Conflicting Sources Detected</p>
                    <p className="text-orange-200/70 text-xs">{msg.conflict_note}</p>
                  </div>
                </div>
              )}

              {/* Answer */}
              <div className="prose-campus text-sm">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
              </div>
            </>
          )}
        </div>

        {/* Citations */}
        {!isUser && msg.citations && msg.citations.length > 0 && (
          <CitationPanel citations={msg.citations} />
        )}

        {/* Action bar */}
        {!isUser && (
          <div className="flex items-center gap-3 px-1">
            {msg.processing_time_ms && (
              <span className="text-slate-600 text-xs">{msg.processing_time_ms.toFixed(0)}ms</span>
            )}
            <button
              onClick={copyToClipboard}
              className="text-slate-500 hover:text-slate-300 transition-colors"
              title="Copy answer"
            >
              <Copy className="w-3.5 h-3.5" />
            </button>
            {onRetry && (
              <button
                onClick={onRetry}
                className="text-slate-500 hover:text-slate-300 transition-colors"
                title="Retry"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Empty state ───────────────────────────────────────────────────────────────
function EmptyState({ onSuggest }: { onSuggest: (q: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full py-12 px-6 text-center">
      <div className="w-16 h-16 rounded-2xl bg-teal-500/10 border border-teal-500/20 
                      flex items-center justify-center mb-6">
        <GraduationCapIcon className="w-8 h-8 text-teal-400" />
      </div>
      <h2 className="text-xl font-semibold text-slate-200 mb-2">Ask anything about your university</h2>
      <p className="text-slate-500 text-sm mb-8 max-w-md">
        CampusSaarthi retrieves answers from campus documents and cites its sources.
        Try one of these questions to get started:
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-xl">
        {SUGGESTED_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => onSuggest(q)}
            className="text-left px-4 py-3 bg-slate-800/50 hover:bg-slate-800 
                       border border-slate-700/50 hover:border-teal-500/30
                       rounded-xl text-slate-300 text-sm transition-all duration-200"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}

function GraduationCapIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
      <path d="M6 12v5c3 3 9 3 12 0v-5" />
    </svg>
  )
}

// ── Main chat interface ───────────────────────────────────────────────────────
export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | undefined>()
  const [lastQuestion, setLastQuestion] = useState<string>('')

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const submit = useCallback(async (question: string) => {
    if (!question.trim() || loading) return
    setLastQuestion(question)
    setInput('')

    const userMsg: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: question.trim(),
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    try {
      // Build conversation history (last 6 turns)
      const history = messages.slice(-6).map((m) => ({ role: m.role, content: m.content }))

      const res = await sendChat(question.trim(), conversationId, history)
      setConversationId(res.conversation_id)

      const assistantMsg: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: res.answer,
        citations: res.citations,
        abstained: res.abstained,
        abstention_reason: res.abstention_reason,
        conflict_detected: res.conflict_detected,
        conflict_note: res.conflict_note,
        processing_time_ms: res.processing_time_ms,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : 'Network error'
      toast.error(errMsg)
      const errorMsg: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: `⚠️ Error: ${errMsg}. Please try again.`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [loading, messages, conversationId])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit(input)
    }
  }

  const clearChat = () => {
    setMessages([])
    setConversationId(undefined)
    setInput('')
    inputRef.current?.focus()
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {messages.length === 0 ? (
          <EmptyState onSuggest={(q) => { setInput(q); inputRef.current?.focus() }} />
        ) : (
          <>
            {messages.map((msg, i) => (
              <ChatBubble
                key={msg.id}
                msg={msg}
                onRetry={
                  msg.role === 'assistant' && i === messages.length - 1
                    ? () => submit(lastQuestion)
                    : undefined
                }
              />
            ))}
            {loading && <TypingIndicator />}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-slate-800/50 p-4 bg-slate-900/50 backdrop-blur-sm">
        {messages.length > 0 && (
          <div className="flex justify-end mb-2">
            <button
              onClick={clearChat}
              className="text-xs text-slate-500 hover:text-slate-300 transition-colors flex items-center gap-1"
            >
              <RotateCcw className="w-3 h-3" /> Clear chat
            </button>
          </div>
        )}
        <div className="flex gap-3 items-end max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              id="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about exams, fees, registration, courses…"
              rows={1}
              className="w-full resize-none bg-slate-800/60 border border-slate-700/50 rounded-xl 
                         px-4 py-3 pr-12 text-slate-100 placeholder:text-slate-500 text-sm
                         input-ring transition-all duration-200 min-h-[48px] max-h-[160px]"
              style={{ height: 'auto' }}
              onInput={(e) => {
                const t = e.currentTarget
                t.style.height = 'auto'
                t.style.height = `${Math.min(t.scrollHeight, 160)}px`
              }}
              disabled={loading}
              aria-label="Ask a question"
            />
          </div>
          <button
            id="send-btn"
            onClick={() => submit(input)}
            disabled={!input.trim() || loading}
            aria-label="Send message"
            className="w-12 h-12 rounded-xl bg-teal-500 hover:bg-teal-400 disabled:bg-slate-700 
                       disabled:text-slate-500 text-slate-950 flex items-center justify-center
                       transition-all duration-200 hover:shadow-lg hover:shadow-teal-500/25 shrink-0"
          >
            {loading
              ? <Loader2 className="w-5 h-5 animate-spin text-teal-300" />
              : <Send className="w-5 h-5" />}
          </button>
        </div>
        <p className="text-xs text-slate-600 text-center mt-2">
          Enter to send · Shift+Enter for new line · Answers grounded in campus documents only
        </p>
      </div>
    </div>
  )
}

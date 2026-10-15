import type { Metadata } from 'next'
import Sidebar from '@/components/Sidebar'
import ChatInterface from '@/components/ChatInterface'

export const metadata: Metadata = {
  title: 'Chat – CampusSaarthi AI',
  description: 'Ask questions about exams, fees, registration, and campus procedures.',
}

export default function ChatPage() {
  return (
    <div className="flex h-screen bg-slate-950 overflow-hidden">
      {/* Demo banner */}
      <div className="absolute top-0 left-0 right-0 z-50 demo-banner">
        ⚠️ DEMO MODE — Synthetic documents only. Not official university policy.
      </div>

      <Sidebar className="mt-8" />

      <main className="flex-1 flex flex-col overflow-hidden mt-8">
        <header className="px-6 py-3 border-b border-slate-800/50 flex items-center gap-3">
          <h1 className="font-semibold text-slate-200">Campus Knowledge Chat</h1>
          <span className="text-xs px-2 py-0.5 bg-teal-500/10 text-teal-400 border border-teal-500/20 rounded-full">
            RAG-powered
          </span>
        </header>

        <div className="flex-1 overflow-hidden">
          <ChatInterface />
        </div>
      </main>
    </div>
  )
}

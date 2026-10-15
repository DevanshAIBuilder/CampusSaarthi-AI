'use client'

import Link from 'next/link'
import {
  BookOpen, Search, Shield, Zap, MessageSquare,
  FileText, CheckCircle, AlertTriangle, ArrowRight, GraduationCap,
} from 'lucide-react'

const FEATURES = [
  {
    icon: <Shield className="w-6 h-6 text-teal-400" />,
    title: 'Grounded Answers',
    desc: 'Every answer is sourced directly from official campus documents with page-level citations.',
  },
  {
    icon: <Search className="w-6 h-6 text-teal-400" />,
    title: 'Smart Retrieval',
    desc: 'Semantic search finds the most relevant document passages, not just keyword matches.',
  },
  {
    icon: <AlertTriangle className="w-6 h-6 text-amber-400" />,
    title: 'Transparent Uncertainty',
    desc: 'When the answer isn\'t in the documents, we say so explicitly — no hallucinated policies.',
  },
  {
    icon: <FileText className="w-6 h-6 text-teal-400" />,
    title: 'Source Citations',
    desc: 'See exactly which document and page number backs every answer you receive.',
  },
  {
    icon: <MessageSquare className="w-6 h-6 text-teal-400" />,
    title: 'Follow-up Questions',
    desc: 'Ask multi-turn follow-ups and CampusSaarthi maintains context across the conversation.',
  },
  {
    icon: <Zap className="w-6 h-6 text-cyan-400" />,
    title: 'Fast RAG Pipeline',
    desc: 'FAISS vector search with Sentence Transformers delivers results in under a second.',
  },
]

const TOPICS = [
  '📅 Exam schedules and admit cards',
  '💰 Fee structure and payment deadlines',
  '📋 Registration and enrollment procedures',
  '📚 Course materials and resources',
  '🏫 Administrative procedures',
  '📝 Re-appear and supplementary exams',
]

export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-950">
      {/* Demo Data Banner */}
      <div className="demo-banner">
        ⚠️ DEMO MODE — Documents are synthetic illustrative content, not official Integral University policies.
      </div>

      {/* Hero */}
      <section className="relative overflow-hidden px-6 pt-20 pb-24">
        {/* Background glow */}
        <div className="absolute inset-0 bg-gradient-to-br from-teal-950/30 via-slate-950 to-navy-950/30 pointer-events-none" />
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-teal-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-4xl mx-auto text-center">
          {/* Logo mark */}
          <div className="inline-flex items-center gap-3 mb-8 px-4 py-2 bg-teal-500/10 border border-teal-500/20 rounded-full">
            <GraduationCap className="w-5 h-5 text-teal-400" />
            <span className="text-teal-300 text-sm font-medium">Hacktoberfest Hack Day 2026 — Integral University</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight">
            <span className="gradient-text">CampusSaarthi</span>
            <span className="text-slate-100"> AI</span>
          </h1>

          <p className="text-xl md:text-2xl text-slate-400 mb-4 text-balance leading-relaxed">
            Your university knowledge assistant.
            <br className="hidden md:block" />
            <span className="text-slate-300"> Instant, document-grounded answers with verified citations.</span>
          </p>

          <p className="text-slate-500 mb-10 max-w-2xl mx-auto">
            Ask about exams, fees, registration, courses, and campus procedures.
            CampusSaarthi retrieves answers from official documents and cites its sources—
            or clearly says when it can't find the answer.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/chat"
              id="start-asking-btn"
              className="inline-flex items-center gap-2 px-8 py-4 bg-teal-500 hover:bg-teal-400 
                         text-slate-950 font-semibold rounded-xl transition-all duration-200 
                         hover:shadow-lg hover:shadow-teal-500/25 hover:-translate-y-0.5"
            >
              Start Asking
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/admin"
              id="admin-panel-btn"
              className="inline-flex items-center gap-2 px-8 py-4 bg-slate-800 hover:bg-slate-700 
                         text-slate-200 font-semibold rounded-xl border border-slate-700 
                         transition-all duration-200 hover:-translate-y-0.5"
            >
              Admin Dashboard
              <FileText className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* What can you ask */}
      <section className="px-6 py-16 max-w-5xl mx-auto">
        <h2 className="text-2xl font-bold text-slate-200 mb-2 text-center">What can I ask?</h2>
        <p className="text-slate-500 text-center mb-10">CampusSaarthi covers the most common student queries</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {TOPICS.map((topic) => (
            <div
              key={topic}
              className="glass-card px-4 py-3 text-slate-300 text-sm flex items-center gap-2 
                         hover:border-teal-500/30 transition-colors duration-200"
            >
              {topic}
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="px-6 py-16 bg-slate-900/30">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-slate-200 mb-2 text-center">Built for reliability</h2>
          <p className="text-slate-500 text-center mb-12">
            No hallucinations. No invented policies. Just grounded, citable answers.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f) => (
              <div key={f.title} className="glass-card p-6 hover:border-slate-600/50 transition-colors duration-200">
                <div className="mb-4">{f.icon}</div>
                <h3 className="font-semibold text-slate-200 mb-2">{f.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="px-6 py-16 max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-slate-200 mb-10 text-center">How it works</h2>
        <div className="space-y-4">
          {[
            { step: '01', title: 'You ask a question', desc: 'Type your query naturally in the chat interface.' },
            { step: '02', title: 'Semantic retrieval', desc: 'CampusSaarthi embeds your question and searches the campus document index using FAISS vector similarity.' },
            { step: '03', title: 'Evidence-grounded generation', desc: 'An open-weight language model reads only the retrieved passages and composes a factual answer — citing each source.' },
            { step: '04', title: 'Citation validation', desc: 'Every inline citation [1][2] is validated against actual retrieved passages. Hallucinated references are removed.' },
            { step: '05', title: 'Transparent abstention', desc: 'If the documents don\'t contain the answer, the system says so clearly rather than guessing.' },
          ].map((item) => (
            <div key={item.step} className="flex gap-4 glass-card p-5">
              <span className="text-3xl font-bold text-teal-500/30 font-mono shrink-0">{item.step}</span>
              <div>
                <h3 className="font-semibold text-slate-200 mb-1">{item.title}</h3>
                <p className="text-slate-400 text-sm">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Disclaimer */}
      <section className="px-6 py-10 border-t border-slate-800/50">
        <div className="max-w-4xl mx-auto">
          <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-6">
            <div className="flex gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-amber-300 mb-2">Important Disclaimer</h3>
                <p className="text-amber-200/70 text-sm leading-relaxed">
                  This application uses <strong className="text-amber-200">synthetic demo documents</strong> created
                  for the Hacktoberfest Hack Day 2026. All fee amounts, exam dates, procedures, and
                  deadlines are <strong className="text-amber-200">illustrative only</strong> and do not represent
                  official Integral University policies. Do not use this information for actual academic or
                  financial decisions. Contact the university administration for official information.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-8 border-t border-slate-800/50 text-center text-slate-600 text-sm">
        <p>CampusSaarthi AI — Built for Hacktoberfest Hack Day 2026 at Integral University, Lucknow</p>
        <p className="mt-1">Open-weight RAG · FAISS · Sentence Transformers · Next.js · FastAPI</p>
      </footer>
    </main>
  )
}

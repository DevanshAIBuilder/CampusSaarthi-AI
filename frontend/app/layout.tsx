import type { Metadata } from 'next'
import './globals.css'
import { Toaster } from 'react-hot-toast'

export const metadata: Metadata = {
  title: 'CampusSaarthi AI – University Knowledge Assistant',
  description:
    'Get instant, document-grounded answers to your university questions. Powered by RAG and verified campus documents.',
  keywords: ['university', 'AI', 'knowledge assistant', 'Integral University', 'campus', 'RAG'],
  openGraph: {
    title: 'CampusSaarthi AI',
    description: 'University Knowledge Assistant with verified citations',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased">
        {children}
        <Toaster
          position="bottom-right"
          toastOptions={{
            className: '!bg-slate-800 !text-slate-100 !border !border-slate-700',
            duration: 4000,
          }}
        />
      </body>
    </html>
  )
}

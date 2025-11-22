import type { Metadata } from 'next'
import './globals.css'
import { CodyMascot } from '@/components/CodyMascot'
import { CodyChatPanel } from '@/components/CodyChatPanel'

export const metadata: Metadata = {
  title: 'FileCherry Appliance',
  description: 'AI-powered file processing appliance',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-neutral-950 text-neutral-50 flex flex-col">
          {/* Top bar */}
          <header className="border-b border-neutral-900 bg-neutral-950/90 backdrop-blur-md">
            <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <CodyMascot size="sm" />
                <div className="flex flex-col leading-tight">
                  <span className="text-sm font-semibold">
                    FileCherry Appliance
                  </span>
                  <span className="text-[11px] text-neutral-400">
                    Offline AI box · inputs in, cherries out.
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-3 text-[11px] text-neutral-400">
                <div className="hidden sm:flex flex-col text-right">
                  <span>Data dir: <code className="text-[10px] text-neutral-300">/data</code></span>
                  <span>UI running on <code className="text-[10px] text-neutral-300">localhost:3000</code></span>
                </div>
              </div>
            </div>
          </header>

          {/* Main content area */}
          <main className="flex-1">
            <div className="mx-auto max-w-6xl px-4 py-6">
              {children}
            </div>
          </main>

          {/* Cody chat bubble in the corner */}
          <CodyChatPanel />
        </div>
      </body>
    </html>
  )
}


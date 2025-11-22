'use client'

import { useState } from 'react'
import { CodyMascot } from './CodyMascot'

type Role = 'user' | 'assistant'

interface ChatMessage {
  role: Role
  content: string
}

interface CodyChatPanelProps {
  defaultOpen?: boolean
}

export function CodyChatPanel({ defaultOpen = false }: CodyChatPanelProps) {
  const [open, setOpen] = useState(defaultOpen)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        "I'm Cody. You dump files in `inputs/`, I drag them through the machinery. What do you want to know?",
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  async function sendMessage() {
    const trimmed = input.trim()
    if (!trimmed || loading) return

    const nextMessages: ChatMessage[] = [
      ...messages,
      { role: 'user', content: trimmed },
    ]

    setMessages(nextMessages)
    setInput('')
    setLoading(true)

    try {
      const resp = await fetch('/api/cody/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: nextMessages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      })

      if (!resp.ok) throw new Error('Cody is not answering.')

      const data = await resp.json()
      const reply: string = data.reply ?? '(no reply)'

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: reply },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'Cody dropped a sack on that one. The chat backend might be down – check the orchestrator logs or Ollama service.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="fixed bottom-4 right-4 z-40">
      {/* Toggle button */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-full bg-neutral-900/90 border border-neutral-700 px-4 py-2 text-xs font-medium shadow-lg hover:bg-neutral-800 transition"
      >
        <CodyMascot size="sm" />
        <span>{open ? 'Close Cody chat' : 'Chat with Cody'}</span>
      </button>

      {/* Panel */}
      {open && (
        <div className="mt-3 w-[320px] sm:w-[380px] rounded-2xl border border-neutral-800 bg-neutral-950/95 shadow-2xl backdrop-blur flex flex-col max-h-[60vh] overflow-hidden">
          <div className="flex items-center gap-2 px-3 py-2 border-b border-neutral-800">
            <CodyMascot size="sm" />
            <div className="flex flex-col">
              <span className="text-xs font-semibold">Cody the Cherry Picker</span>
              <span className="text-[11px] text-neutral-400">
                Ask how to use FileCherry, read logs, or fix stuff.
              </span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2 text-xs">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex ${
                  m.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3 py-2 ${
                    m.role === 'user'
                      ? 'bg-amber-400 text-neutral-950'
                      : 'bg-neutral-900 text-neutral-100 border border-neutral-800'
                  } whitespace-pre-wrap`}
                >
                  {m.content}
                </div>
              </div>
            ))}

            {loading && (
              <div className="text-[11px] text-neutral-500">
                Cody is thinking really hard for someone with dot eyes…
              </div>
            )}
          </div>

          <div className="border-t border-neutral-800 p-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={2}
              className="w-full resize-none rounded-xl bg-neutral-900 text-xs text-neutral-100 px-3 py-2 outline-none border border-neutral-700 focus:border-amber-400"
              placeholder='"Cody, why did that job fail?" or "How do I structure inputs for car photos?"'
            />

            <div className="flex justify-end pt-1">
              <button
                type="button"
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                className="rounded-full bg-amber-400 text-neutral-950 text-[11px] font-semibold px-3 py-1.5 disabled:opacity-60 disabled:cursor-not-allowed hover:bg-amber-300 transition"
              >
                {loading ? 'Working...' : 'Send'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


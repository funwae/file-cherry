'use client'

import { useState, useEffect } from 'react'
import { CodyMascot } from './CodyMascot'

interface CodyFirstJobIntroProps {
  open: boolean
  onClose: () => void
}

const ONBOARDING_KEY = 'filecherry:seen-onboarding'

export function CodyFirstJobIntro({ open, onClose }: CodyFirstJobIntroProps) {
  const [step, setStep] = useState(1)

  useEffect(() => {
    if (!open) return

    // Check if user has seen onboarding
    const hasSeen = localStorage.getItem(ONBOARDING_KEY)
    if (hasSeen === 'true') {
      onClose()
    }
  }, [open, onClose])

  if (!open) return null

  const isFirst = step === 1
  const isLast = step === 3

  const next = () => setStep((s) => Math.min(3, s + 1))
  const prev = () => setStep((s) => Math.max(1, s - 1))

  const handleClose = () => {
    localStorage.setItem(ONBOARDING_KEY, 'true')
    onClose()
  }

  const handleFinish = () => {
    handleClose()
    // Focus the intent textarea if it exists
    setTimeout(() => {
      const textarea = document.querySelector('textarea[id="intent"]') as HTMLTextAreaElement
      if (textarea) {
        textarea.focus()
      }
    }, 100)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-3xl rounded-2xl border border-neutral-800 bg-neutral-950 px-6 py-5 shadow-2xl flex flex-col md:flex-row gap-6">
        <div className="flex flex-col items-center md:items-start gap-3 md:w-1/3">
          <CodyMascot size="lg" />
          <div className="text-xs font-semibold uppercase tracking-wide text-neutral-400">
            Cody&apos;s first job
          </div>
          <div className="flex gap-1 mt-1">
            {[1, 2, 3].map((n) => (
              <span
                key={n}
                className={`h-1.5 w-5 rounded-full ${
                  n === step ? 'bg-amber-400' : 'bg-neutral-700'
                }`}
              />
            ))}
          </div>
        </div>

        <div className="md:w-2/3 flex flex-col justify-between gap-4 text-sm">
          <div className="space-y-3">
            {step === 1 && (
              <>
                <h2 className="text-lg font-semibold">Here&apos;s the deal.</h2>
                <p className="text-neutral-300">
                  This isn&apos;t a website. It&apos;s a little OS on a stick.
                  You dump files into <code className="bg-neutral-800 px-1.5 py-0.5 rounded">inputs/</code>, boot from this thing,
                  and I drag them through AI pipelines. When I&apos;m done, your
                  cherries are stacked in <code className="bg-neutral-800 px-1.5 py-0.5 rounded">outputs/</code>.
                </p>
                <ul className="list-disc list-inside text-neutral-300 space-y-1 ml-2">
                  <li>
                    On your <em>normal</em> computer: plug in the stick and drop files
                    into <code className="bg-neutral-800 px-1 py-0.5 rounded text-xs">inputs/</code>.
                  </li>
                  <li>
                    In here: I scan <code className="bg-neutral-800 px-1 py-0.5 rounded text-xs">inputs/</code>, plan a job, and run
                    Ollama + ComfyUI + doc tools.
                  </li>
                  <li>
                    When I&apos;m done, everything&apos;s in{' '}
                    <code className="bg-neutral-800 px-1 py-0.5 rounded text-xs">outputs/&lt;job-id&gt;/</code>.
                  </li>
                </ul>
                <p className="text-xs text-neutral-500 italic">
                  If you remember nothing else: <b>inputs in, outputs out.</b>{' '}
                  I&apos;m everything in the middle.
                </p>
              </>
            )}

            {step === 2 && (
              <>
                <h2 className="text-lg font-semibold">
                  Tell me what you want done.
                </h2>
                <p className="text-neutral-300">
                  See that big text box on the main screen? That&apos;s where
                  you boss me around. You don&apos;t have to speak &quot;AI&quot;.
                  Just say what you want done with the files you dumped.
                </p>
                <div className="space-y-2 text-neutral-300">
                  <div className="text-xs font-semibold text-neutral-400 uppercase tracking-wide">
                    Example jobs:
                  </div>
                  <div className="space-y-1.5">
                    <div className="bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-2 text-xs">
                      &quot;Clean up all car photos and make them ready for
                      listings.&quot;
                    </div>
                    <div className="bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-2 text-xs">
                      &quot;Read all PDFs, group by topic, and give me a summary
                      for leadership.&quot;
                    </div>
                    <div className="bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-2 text-xs">
                      &quot;Search across everything for anything about
                      &apos;warranty claims&apos; and summarize it.&quot;
                    </div>
                  </div>
                </div>
                <p className="text-xs text-neutral-500 italic">
                  You can always open the <b>Chat with Cody</b> bubble in the
                  corner and ask, &quot;What are you doing to my files right
                  now?&quot;
                </p>
              </>
            )}

            {step === 3 && (
              <>
                <h2 className="text-lg font-semibold">
                  When I drop a sack.
                </h2>
                <p className="text-neutral-300">
                  Sometimes jobs fail. Models crash. Disks fill up. It happens.
                  When something goes sideways, here&apos;s where you look
                  first:
                </p>
                <ul className="list-disc list-inside text-neutral-300 space-y-1 ml-2">
                  <li>
                    Check the <b>job status</b> in the UI to see which step blew up.
                  </li>
                  <li>
                    Look at <code className="bg-neutral-800 px-1 py-0.5 rounded text-xs">/data/logs/</code> (or <code className="bg-neutral-800 px-1 py-0.5 rounded text-xs">logs/</code> on
                    the data partition) for details.
                  </li>
                  <li>
                    Ask me in chat: &quot;Cody, why did that job fail?&quot; or
                    &quot;Is Ollama running?&quot;
                  </li>
                </ul>
                <p className="text-xs text-neutral-500 italic">
                  Worst case, nothing gets deleted. Your{' '}
                  <code className="bg-neutral-800 px-1 py-0.5 rounded">inputs/</code> are still there. Fix the issue, run the
                  job again, and I&apos;ll pretend I&apos;m not offended.
                </p>
              </>
            )}
          </div>

          <div className="flex justify-between items-center pt-2 border-t border-neutral-800">
            <button
              type="button"
              className="text-xs text-neutral-500 hover:text-neutral-300 transition"
              onClick={handleClose}
            >
              Skip intro
            </button>
            <div className="flex gap-2">
              {!isFirst && (
                <button
                  type="button"
                  onClick={prev}
                  className="text-xs rounded-full border border-neutral-700 px-3 py-1.5 hover:bg-neutral-900 transition"
                >
                  Back
                </button>
              )}
              <button
                type="button"
                onClick={isLast ? handleFinish : next}
                className="text-xs rounded-full bg-amber-400 text-neutral-950 px-3 py-1.5 font-semibold hover:bg-amber-300 transition"
              >
                {isLast ? "Let's do my first job" : 'Next'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}


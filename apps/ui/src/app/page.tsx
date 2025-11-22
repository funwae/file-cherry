'use client'

import { useState, useEffect } from 'react'
import { CodyMascot } from '@/components/CodyMascot'
import PlanPreviewScreen from '@/components/PlanPreviewScreen'
import JobProgressScreen from '@/components/JobProgressScreen'
import CompletionScreen from '@/components/CompletionScreen'
import { CodyFirstJobIntro } from '@/components/CodyFirstJobIntro'

type Screen = 'intro' | 'plan' | 'progress' | 'completion'

interface Inventory {
  total_files: number
  type_counts: Record<string, number>
  items?: Array<{ path: string; type: string }>
}

interface InputsSummary {
  totalFiles: number
  imageCount: number
  docCount: number
  otherCount: number
}

export default function Home() {
  const [screen, setScreen] = useState<Screen>('intro')
  const [inventory, setInventory] = useState<Inventory | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [plan, setPlan] = useState<any>(null)
  const [intent, setIntent] = useState<string>('')
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    // Load inventory on mount
    fetch('/api/inventory')
      .then(res => res.json())
      .then(data => setInventory(data))
      .catch(err => console.error('Error loading inventory:', err))

    // Check if we should show onboarding
    const hasSeenOnboarding = localStorage.getItem('filecherry:seen-onboarding')
    const hasJobs = false // TODO: Check if there are any completed jobs
    if (!hasSeenOnboarding && !hasJobs) {
      setShowOnboarding(true)
    }
  }, [])

  const handleSubmitIntent = async (userIntent: string) => {
    setIntent(userIntent)
    setIsSubmitting(true)
    try {
      const response = await fetch('/api/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ intent: userIntent }),
      })
      const data = await response.json()
      setJobId(data.job_id)

      // Fetch plan from job manifest
      if (data.job_id) {
        fetchPlan(data.job_id)
      }

      setScreen('plan')
    } catch (error) {
      console.error('Error creating job:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const fetchPlan = async (id: string) => {
    try {
      const response = await fetch(`/api/jobs/${id}/manifest`)
      const manifest = await response.json()
      if (manifest.plan) {
        setPlan(manifest.plan)
      }
    } catch (error) {
      console.error('Error fetching plan:', error)
    }
  }

  const handleRunJob = () => {
    setScreen('progress')
    // Start polling for job status
    if (jobId) {
      pollJobStatus(jobId)
    }
  }

  const handleEditPlan = () => {
    setScreen('intro')
  }

  const pollJobStatus = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/jobs/${id}`)
        const job = await response.json()

        if (job.status === 'completed' || job.status === 'failed') {
          clearInterval(interval)
          setScreen('completion')
        }
      } catch (error) {
        console.error('Error polling job status:', error)
        clearInterval(interval)
      }
    }, 2000) // Poll every 2 seconds
  }

  // Calculate inputs summary from inventory
  const getInputsSummary = (): InputsSummary => {
    if (!inventory) {
      return { totalFiles: 0, imageCount: 0, docCount: 0, otherCount: 0 }
    }

    const typeCounts = inventory.type_counts || {}
    const imageCount = (typeCounts.image || 0) + (typeCounts.images || 0)
    const docCount = (typeCounts.document || 0) + (typeCounts.documents || 0) +
                     (typeCounts.pdf || 0) + (typeCounts.docx || 0) +
                     (typeCounts.txt || 0) + (typeCounts.html || 0)
    const otherCount = inventory.total_files - imageCount - docCount

    return {
      totalFiles: inventory.total_files || 0,
      imageCount,
      docCount,
      otherCount: Math.max(0, otherCount),
    }
  }

  const inputs = getInputsSummary()
  const hasInputs = inputs.totalFiles > 0

  // Show other screens when not on intro
  if (screen === 'plan') {
    return (
      <>
        <PlanPreviewScreen
          plan={plan}
          intent={intent}
          onRun={handleRunJob}
          onEdit={handleEditPlan}
        />
        <CodyFirstJobIntro
          open={showOnboarding}
          onClose={() => setShowOnboarding(false)}
        />
      </>
    )
  }

  if (screen === 'progress' && jobId) {
    return (
      <>
        <JobProgressScreen jobId={jobId} />
        <CodyFirstJobIntro
          open={showOnboarding}
          onClose={() => setShowOnboarding(false)}
        />
      </>
    )
  }

  if (screen === 'completion' && jobId) {
    return (
      <>
        <CompletionScreen jobId={jobId} />
        <CodyFirstJobIntro
          open={showOnboarding}
          onClose={() => setShowOnboarding(false)}
        />
      </>
    )
  }

  // Main dashboard (intro screen)
  return (
    <>
      <div className="grid gap-6 md:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        {/* LEFT: Job console */}
        <section className="space-y-4">
          <header className="space-y-1">
            <h1 className="text-xl font-semibold">
              What do you want to do with these files?
            </h1>
            <p className="text-sm text-neutral-400">
              Files in <code className="text-neutral-300">inputs/</code> on the data partition are ready to go.
              Describe the job in plain English — Cody and the orchestrator will
              figure out the pipelines.
            </p>
          </header>

          <div className="rounded-2xl border border-neutral-900 bg-neutral-900/70 p-4">
            <form
              onSubmit={(e) => {
                e.preventDefault()
                if (intent.trim() && !isSubmitting) {
                  handleSubmitIntent(intent)
                }
              }}
            >
              <textarea
                value={intent}
                onChange={(e) => setIntent(e.target.value)}
                rows={5}
                className="w-full resize-none rounded-xl bg-neutral-950/60 border border-neutral-800 focus:border-amber-400 outline-none px-3 py-2 text-sm text-neutral-100 placeholder:text-neutral-500"
                placeholder={
                  hasInputs
                    ? 'Example: "Clean up all car photos and make them ready for listings."'
                    : 'Drop some files into inputs/ on the USB, then try: "Read all PDFs and summarize by topic."'
                }
                disabled={isSubmitting || !hasInputs}
              />
              <div className="mt-3 flex items-center justify-between gap-3 text-[11px] text-neutral-400">
                <span>
                  Tip: mention what&apos;s in <code>inputs/</code> and what you
                  want out in <code>outputs/</code>.
                </span>
                <button
                  type="submit"
                  disabled={isSubmitting || !intent.trim() || !hasInputs}
                  className="rounded-full bg-amber-400 text-neutral-950 px-4 py-1.5 text-[11px] font-semibold hover:bg-amber-300 transition disabled:bg-neutral-700 disabled:text-neutral-500 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Processing...' : 'Run job'}
                </button>
              </div>
            </form>
          </div>

          {/* Inputs/outputs status */}
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-neutral-900 bg-neutral-900/70 p-4 text-sm">
              <div className="flex items-center justify-between gap-2">
                <span className="font-semibold">inputs/ status</span>
                <span className="text-[11px] text-neutral-500">/data/inputs</span>
              </div>
              <div className="mt-2 text-neutral-300">
                {hasInputs ? (
                  <ul className="space-y-1 text-[13px]">
                    <li>{inputs.totalFiles} files detected</li>
                    {inputs.imageCount > 0 && <li>{inputs.imageCount} image(s)</li>}
                    {inputs.docCount > 0 && <li>{inputs.docCount} document(s)</li>}
                    {inputs.otherCount > 0 && <li>{inputs.otherCount} other file(s)</li>}
                  </ul>
                ) : (
                  <p className="text-[13px]">
                    No files yet. On your regular OS, plug in the stick and drop
                    files into <code>inputs/</code>. Then come back here.
                  </p>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-neutral-900 bg-neutral-900/70 p-4 text-sm">
              <div className="flex items-center justify-between gap-2">
                <span className="font-semibold">Recent jobs</span>
                <span className="text-[11px] text-neutral-500">outputs/</span>
              </div>
              <div className="mt-2 text-[13px] text-neutral-300">
                {/* TODO: Wire to real job list */}
                <p>No jobs yet. Cody is standing here with ten bags of cherries and nothing to do.</p>
              </div>
            </div>
          </div>
        </section>

        {/* RIGHT: Cody status / onboarding */}
        <aside className="space-y-4">
          <div className="rounded-2xl border border-neutral-900 bg-neutral-900/70 p-4 flex flex-col items-center gap-3">
            <CodyMascot size="md" mood={hasInputs ? 'idle' : 'loading'} />
            <div className="text-xs text-neutral-300 text-center">
              {hasInputs ? (
                <>
                  <p>
                    &quot;You bring the chaos, I haul it. Tell me what you want done
                    and I&apos;ll drag it through the machinery.&quot;
                  </p>
                </>
              ) : (
                <>
                  <p>
                    &quot;Stick&apos;s plugged in, but <code>inputs/</code> is empty.
                    Drop something in there so I don&apos;t feel useless.&quot;
                  </p>
                </>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-neutral-900 bg-neutral-900/70 p-4 text-[12px] text-neutral-300 space-y-2">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-neutral-400">
              First time here?
            </div>
            <p>
              The loop is simple: on your normal OS, copy files into{' '}
              <code>inputs/</code>. Boot from this stick. Describe the job. When
              I&apos;m done, grab the results from <code>outputs/&lt;job-id&gt;/</code>.
            </p>
            <p className="text-neutral-500">
              If anything explodes, open the chat bubble in the corner and ask:
              &quot;Cody, what broke?&quot;
            </p>
          </div>
        </aside>
      </div>

      {/* Onboarding - show on first visit */}
      <CodyFirstJobIntro
        open={showOnboarding}
        onClose={() => setShowOnboarding(false)}
      />
    </>
  )
}


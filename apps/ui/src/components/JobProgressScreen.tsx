'use client'

import { useState, useEffect } from 'react'

interface JobProgressScreenProps {
  jobId: string
}

interface Step {
  name: string
  type: string
  status: string
  inputs?: string[]
  outputs?: string[]
  error?: string
}

interface JobStatus {
  job_id: string
  status: string
  manifest?: {
    steps: Step[]
    plan?: {
      summary: string
    }
  }
}

export default function JobProgressScreen({ jobId }: JobProgressScreenProps) {
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null)
  const [showLogs, setShowLogs] = useState(false)

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/jobs/${jobId}`)
        const data = await response.json()
        setJobStatus(data)
      } catch (error) {
        console.error('Error fetching job status:', error)
      }
    }, 2000) // Poll every 2 seconds

    return () => clearInterval(interval)
  }, [jobId])

  const steps = jobStatus?.manifest?.steps || []
  const currentStatus = jobStatus?.status || 'unknown'

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return '✓'
      case 'running':
        return '●'
      case 'failed':
        return '✗'
      default:
        return '○'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-400'
      case 'running':
        return 'text-amber-400'
      case 'failed':
        return 'text-red-400'
      default:
        return 'text-neutral-500'
    }
  }

  return (
    <div className="max-w-3xl w-full">
      <div className="rounded-2xl border border-neutral-900 bg-neutral-900/70 p-6">
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-neutral-50 mb-2">
            Processing Job
          </h2>
          <p className="text-sm text-neutral-400">
            Job ID: <code className="bg-neutral-950/60 px-2 py-1 rounded text-neutral-300">{jobId}</code>
          </p>
        </div>

        {jobStatus?.manifest?.plan && (
          <div className="mb-6 p-4 bg-amber-400/10 border border-amber-400/20 rounded-xl">
            <p className="text-amber-300 text-sm">{jobStatus.manifest.plan.summary}</p>
          </div>
        )}

        <div className="space-y-4 mb-6">
          {steps.map((step, idx) => (
            <div key={idx} className="flex items-start p-4 bg-neutral-950/60 rounded-xl border border-neutral-800">
              <span className={`text-2xl mr-4 ${getStatusColor(step.status)}`}>
                {getStatusIcon(step.status)}
              </span>
              <div className="flex-1">
                <p className="font-semibold text-neutral-100">
                  Step {idx + 1}: {step.name || step.type}
                </p>
                {step.status === 'running' && (
                  <p className="text-sm text-neutral-400 mt-1">
                    Running {step.type}...
                  </p>
                )}
                {step.error && (
                  <p className="text-sm text-red-400 mt-1">
                    Error: {step.error}
                  </p>
                )}
                {step.outputs && step.outputs.length > 0 && (
                  <p className="text-xs text-neutral-500 mt-1">
                    {step.outputs.length} output(s) generated
                  </p>
                )}
              </div>
            </div>
          ))}

          {steps.length === 0 && (
            <div className="p-4 bg-amber-400/10 border border-amber-400/20 rounded-xl">
              <p className="text-amber-300">Job is starting...</p>
            </div>
          )}
        </div>

        <div className="flex gap-4">
          <button
            onClick={() => setShowLogs(!showLogs)}
            className="px-4 py-2 bg-neutral-800 text-neutral-300 rounded-lg hover:bg-neutral-700 transition-colors"
          >
            {showLogs ? 'Hide' : 'View'} Logs
          </button>
          {currentStatus === 'running' && (
            <button
              onClick={() => {
                if (confirm('Are you sure you want to cancel this job?')) {
                  fetch(`/api/jobs/${jobId}`, { method: 'POST' })
                }
              }}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Cancel Job
            </button>
          )}
        </div>

        {showLogs && (
          <div className="mt-6 p-4 bg-neutral-950 text-green-400 rounded-xl font-mono text-sm max-h-64 overflow-y-auto border border-neutral-800">
            <p>Logs would appear here...</p>
          </div>
        )}
      </div>
    </div>
  )
}


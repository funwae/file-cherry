'use client'

import { useState, useEffect } from 'react'

interface CompletionScreenProps {
  jobId: string
}

interface JobManifest {
  job_id: string
  status: string
  outputs: {
    images?: string[]
    docs?: string[]
    misc?: string[]
  }
  steps: Array<{
    name: string
    type: string
    status: string
    outputs?: string[]
  }>
}

export default function CompletionScreen({ jobId }: CompletionScreenProps) {
  const [manifest, setManifest] = useState<JobManifest | null>(null)
  const [showFileTree, setShowFileTree] = useState(false)

  useEffect(() => {
    fetch(`/api/jobs/${jobId}/manifest`)
      .then(res => res.json())
      .then(data => setManifest(data))
      .catch(err => console.error('Error fetching manifest:', err))
  }, [jobId])

  const outputs = manifest?.outputs || {}
  const totalImages = outputs.images?.length || 0
  const totalDocs = outputs.docs?.length || 0
  const totalMisc = outputs.misc?.length || 0

  const allOutputs = [
    ...(outputs.images || []),
    ...(outputs.docs || []),
    ...(outputs.misc || []),
  ]

  return (
    <div className="max-w-3xl w-full">
      <div className="rounded-2xl border border-neutral-900 bg-neutral-900/70 p-6 text-center">
        <div className="mb-6">
          <div className="w-16 h-16 bg-green-400/20 border border-green-400/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl text-green-400">✓</span>
          </div>
          <h2 className="text-2xl font-semibold text-neutral-50 mb-2">
            Job Complete
          </h2>
          <p className="text-neutral-400">
            Your files have been processed successfully
          </p>
        </div>

        <div className="mb-6 p-6 bg-neutral-950/60 rounded-xl border border-neutral-800">
          <div className="grid grid-cols-3 gap-4 text-center">
            {totalImages > 0 && (
              <div>
                <p className="text-2xl font-bold text-amber-400">{totalImages}</p>
                <p className="text-sm text-neutral-400">Images</p>
              </div>
            )}
            {totalDocs > 0 && (
              <div>
                <p className="text-2xl font-bold text-amber-400">{totalDocs}</p>
                <p className="text-sm text-neutral-400">Documents</p>
              </div>
            )}
            {totalMisc > 0 && (
              <div>
                <p className="text-2xl font-bold text-amber-400">{totalMisc}</p>
                <p className="text-sm text-neutral-400">Other</p>
              </div>
            )}
          </div>
        </div>

        <div className="mb-6 p-4 bg-amber-400/10 border border-amber-400/20 rounded-xl text-left">
          <p className="text-sm text-amber-300">
            <strong>Results saved in:</strong>{' '}
            <code className="bg-neutral-950/60 px-2 py-1 rounded text-amber-200">
              outputs/{jobId}
            </code>
          </p>
        </div>

        <button
          onClick={() => setShowFileTree(!showFileTree)}
          className="mb-6 px-6 py-3 bg-amber-400 text-neutral-950 rounded-lg font-semibold hover:bg-amber-300 transition-colors"
        >
          {showFileTree ? 'Hide' : 'View'} File Tree
        </button>

        {showFileTree && (
          <div className="mb-6 p-4 bg-neutral-950/60 rounded-xl text-left border border-neutral-800">
            <h3 className="font-semibold text-neutral-100 mb-3">Output Files:</h3>
            <div className="space-y-1 font-mono text-sm">
              {allOutputs.length > 0 ? (
                allOutputs.map((path, idx) => (
                  <div key={idx} className="text-neutral-300">
                    {path}
                  </div>
                ))
              ) : (
                <p className="text-neutral-500">No output files found</p>
              )}
            </div>
          </div>
        )}

        <div className="p-4 bg-neutral-950/60 rounded-xl text-left border border-neutral-800">
          <p className="text-sm text-neutral-300">
            <strong>Next steps:</strong> You can now shut down, plug the USB into your usual computer, and open{' '}
            <code className="bg-neutral-900 px-2 py-1 rounded text-amber-300">outputs/{jobId}</code> to access your processed files.
          </p>
        </div>

        <button
          onClick={() => window.location.reload()}
          className="mt-6 px-6 py-3 bg-neutral-800 text-neutral-300 rounded-lg font-semibold hover:bg-neutral-700 transition-colors"
        >
          Start New Job
        </button>
      </div>
    </div>
  )
}


'use client'

import { useState } from 'react'

interface Plan {
  summary: string
  steps: Array<{
    tool: string
    params: Record<string, any>
  }>
}

interface PlanPreviewScreenProps {
  plan: Plan | null
  intent: string
  onRun: () => void
  onEdit: () => void
}

export default function PlanPreviewScreen({
  plan,
  intent,
  onRun,
  onEdit,
}: PlanPreviewScreenProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedIntent, setEditedIntent] = useState(intent)

  const handleEdit = () => {
    setIsEditing(true)
  }

  const handleSaveEdit = () => {
    // In a real implementation, this would trigger re-planning
    setIsEditing(false)
    // For now, just update the display
  }

  return (
    <div className="max-w-3xl w-full">
      <div className="rounded-2xl border border-neutral-900 bg-neutral-900/70 p-6">
        <h2 className="text-xl font-semibold text-neutral-50 mb-6">
          Proposed Plan
        </h2>

        {plan ? (
          <div className="space-y-4 mb-6">
            <div className="p-4 bg-amber-400/10 border border-amber-400/20 rounded-xl">
              <p className="text-amber-300 font-medium">{plan.summary}</p>
              </div>

              <div className="space-y-3">
                {plan.steps.map((step, idx) => (
                  <div key={idx} className="flex items-start p-4 bg-neutral-950/60 rounded-xl border border-neutral-800">
                    <span className="flex-shrink-0 w-8 h-8 bg-amber-400 text-neutral-950 rounded-full flex items-center justify-center font-semibold mr-4">
                      {idx + 1}
                    </span>
                    <div className="flex-1">
                      <p className="font-semibold text-neutral-100 capitalize">
                        {step.tool.replace('_', ' ')}
                      </p>
                      {step.params.purpose && (
                        <p className="text-sm text-neutral-400 mt-1">
                          {step.params.purpose}
                        </p>
                      )}
                      {step.params.query && (
                        <p className="text-sm text-neutral-400 mt-1">
                          {step.params.query}
                        </p>
                      )}
                      {step.params.input_paths && (
                        <p className="text-xs text-neutral-500 mt-1">
                          {step.params.input_paths.length} file(s)
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-4 bg-amber-400/10 border border-amber-400/20 rounded-xl mb-6">
              <p className="text-amber-300">
                Plan is being generated...
              </p>
            </div>
          )}

          {isEditing ? (
            <div className="mb-6">
              <label className="block text-sm font-medium text-neutral-300 mb-2">
                Refine your request:
              </label>
              <textarea
                value={editedIntent}
                onChange={(e) => setEditedIntent(e.target.value)}
                className="w-full px-4 py-3 border border-neutral-800 bg-neutral-950/60 rounded-xl focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none resize-none text-neutral-100 placeholder:text-neutral-500"
                rows={3}
              />
              <div className="flex gap-3 mt-3">
                <button
                  onClick={handleSaveEdit}
                  className="px-4 py-2 bg-amber-400 text-neutral-950 rounded-lg hover:bg-amber-300 font-semibold transition-colors"
                >
                  Save & Re-plan
                </button>
                <button
                  onClick={() => setIsEditing(false)}
                  className="px-4 py-2 bg-neutral-800 text-neutral-300 rounded-lg hover:bg-neutral-700 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="flex gap-4">
              <button
                onClick={handleEdit}
                className="flex-1 px-6 py-3 bg-neutral-800 text-neutral-300 rounded-lg font-semibold hover:bg-neutral-700 transition-colors"
              >
                Edit
              </button>
              <button
                onClick={onRun}
                className="flex-1 px-6 py-3 bg-amber-400 text-neutral-950 rounded-lg font-semibold hover:bg-amber-300 transition-colors"
              >
                Looks good → Run
              </button>
            </div>
          )}
        </div>
    </div>
  )
}


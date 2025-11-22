'use client'

import { useState } from 'react'

interface Inventory {
  total_files: number
  type_counts: Record<string, number>
  items?: Array<{ path: string; type: string }>
}

interface IntroScreenProps {
  inventory: Inventory | null
  onSubmit: (intent: string) => void
}

export default function IntroScreen({ inventory, onSubmit }: IntroScreenProps) {
  const [intent, setIntent] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!intent.trim()) return

    setIsSubmitting(true)
    onSubmit(intent)
    setIsSubmitting(false)
  }

  const typeCounts = inventory?.type_counts || {}
  const totalFiles = inventory?.total_files || 0

  return (
    <div className="flex items-center justify-center min-h-screen p-8">
      <div className="max-w-2xl w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            FileCherry Appliance
          </h1>
          <p className="text-gray-600">
            AI-powered file processing
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8">
          {totalFiles > 0 ? (
            <div className="mb-6">
              <p className="text-lg font-semibold text-gray-800 mb-4">
                Found {totalFiles} file{totalFiles !== 1 ? 's' : ''} in <code className="bg-gray-100 px-2 py-1 rounded">inputs/</code>
              </p>
              <div className="space-y-2 mb-6">
                {Object.entries(typeCounts).map(([type, count]) => (
                  <div key={type} className="flex items-center text-gray-700">
                    <span className="w-24 capitalize">{type}:</span>
                    <span className="font-semibold">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-yellow-800">
                No files found in <code className="bg-yellow-100 px-2 py-1 rounded">inputs/</code>
              </p>
              <p className="text-sm text-yellow-700 mt-2">
                Please add files to the inputs folder and refresh.
              </p>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <label htmlFor="intent" className="block text-sm font-medium text-gray-700 mb-2">
              What do you want to do with these files?
            </label>
            <textarea
              id="intent"
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder="Describe in your own words what you want done. Example: 'Make dealership-ready photos from the images and produce a summary of all the PDFs.'"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              rows={4}
              disabled={isSubmitting || totalFiles === 0}
            />
            <button
              type="submit"
              disabled={isSubmitting || !intent.trim() || totalFiles === 0}
              className="mt-4 w-full bg-primary-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Processing...' : 'Continue'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}


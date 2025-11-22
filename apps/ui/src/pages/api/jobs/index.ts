import type { NextApiRequest, NextApiResponse } from 'next'

const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || 'http://localhost:8000'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === 'POST') {
    // Create new job
    try {
      const { intent } = req.body

      if (!intent || typeof intent !== 'string') {
        return res.status(400).json({ error: 'Intent is required' })
      }

      const response = await fetch(`${ORCHESTRATOR_URL}/api/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ intent }),
      })

      if (!response.ok) {
        throw new Error(`Orchestrator returned ${response.status}`)
      }

      const data = await response.json()
      res.status(200).json(data)
    } catch (error: any) {
      console.error('Error creating job:', error)
      res.status(500).json({
        error: 'Failed to create job',
        message: error.message
      })
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' })
  }
}


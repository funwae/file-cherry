import type { NextApiRequest, NextApiResponse } from 'next'

const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || 'http://localhost:8000'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  const { jobId } = req.query

  if (typeof jobId !== 'string') {
    return res.status(400).json({ error: 'Invalid job ID' })
  }

  try {
    const response = await fetch(`${ORCHESTRATOR_URL}/api/jobs/${jobId}/manifest`)

    if (!response.ok) {
      if (response.status === 404) {
        return res.status(404).json({ error: 'Job not found' })
      }
      throw new Error(`Orchestrator returned ${response.status}`)
    }

    const data = await response.json()
    res.status(200).json(data)
  } catch (error: any) {
    console.error('Error fetching manifest:', error)
    res.status(500).json({
      error: 'Failed to fetch manifest',
      message: error.message
    })
  }
}


import type { NextApiRequest, NextApiResponse } from 'next'

const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || 'http://localhost:8000'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const { messages } = req.body

    if (!messages || !Array.isArray(messages)) {
      return res.status(400).json({ error: 'Messages array is required' })
    }

    const response = await fetch(`${ORCHESTRATOR_URL}/api/cody/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages }),
    })

    if (!response.ok) {
      throw new Error(`Orchestrator returned ${response.status}`)
    }

    const data = await response.json()
    res.status(200).json(data)
  } catch (error: any) {
    console.error('Error in Cody chat:', error)
    res.status(500).json({
      error: 'Failed to chat with Cody',
      message: error.message,
    })
  }
}


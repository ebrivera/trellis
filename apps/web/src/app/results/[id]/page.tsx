'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card } from '../../../components/ui/Card'
import { Button } from '../../../components/ui/Button'
import { Badge } from '../../../components/ui/Badge'
import { CheckCircle2, ArrowLeft, Download, TrendingUp, List } from 'lucide-react'
import type { WorkflowResult } from '@trellis/types'
// MOCK: Import mock data - backend will replace with API calls
import { mockMatchingResult } from '../../../lib/mockData'

export default function ResultsPage() {
  const params = useParams()
  const router = useRouter()
  const [result, setResult] = useState<WorkflowResult | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // MOCK: Using mock data for now
    // TODO: Backend will replace with GET /result/:id API call
    // Real call: const data = await getResult(params.id as string)
    setTimeout(() => {
      setResult(mockMatchingResult)
      setLoading(false)
    }, 500)
  }, [params.id])

  if (loading) {
    return (
      <main className="min-h-screen px-6 pt-32 pb-20">
        <div className="max-w-4xl mx-auto text-center">
          <div className="text-white animate-pulse">Loading results...</div>
        </div>
      </main>
    )
  }

  if (!result) {
    return (
      <main className="min-h-screen px-6 pt-32 pb-20">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-white/70">Result not found</p>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen px-6 pt-32 pb-20">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => router.push('/')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>

          <div className="flex items-start justify-between gap-4 mb-4">
            <div>
              <h1 className="mb-2 text-4xl font-bold text-white">
                Workflow Complete
              </h1>
              <p className="text-lg text-white/70">{result.summary}</p>
            </div>
            <Badge variant="success" className="px-4 py-2 text-lg">
              <CheckCircle2 className="inline-block w-5 h-5 mr-2" />
              {result.status}
            </Badge>
          </div>

          <p className="text-sm text-white/50">
            Completed {new Date(result.completedAt).toLocaleString()}
          </p>
        </div>

        {/* Metrics Cards */}
        <section className="mb-8">
          <h2 className="mb-4 text-2xl font-semibold text-white">Key Metrics</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            {Object.entries(result.metrics).map(([key, value]) => (
              <Card key={key} padding="lg">
                <div className="text-center">
                  <p className="mb-1 text-sm capitalize text-white/60">
                    {key.replace(/([A-Z])/g, ' $1').trim()}
                  </p>
                  <p className="text-3xl font-bold text-white">{value}</p>
                </div>
              </Card>
            ))}
          </div>
        </section>

        {/* Actions Taken */}
        <section className="mb-8">
          <h2 className="mb-4 text-2xl font-semibold text-white">Actions Completed</h2>
          <Card padding="lg">
            <div className="space-y-4">
              {result.actions.map((action, idx) => (
                <div key={idx} className="flex items-start gap-4">
                  <CheckCircle2 className="w-6 h-6 mt-1 text-green-400 shrink-0" />
                  <div className="flex-1">
                    <p className="font-medium text-white">{action.description}</p>
                    <p className="text-sm text-white/60">
                      {action.count} {action.type}{action.count > 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </section>

        {/* Actions */}
        <section className="flex flex-wrap gap-3">
          <Button size="lg">
            <Download className="w-5 h-5 mr-2" />
            Export Report
          </Button>
          <Button variant="outline" size="lg" onClick={() => router.push('/approvals')}>
            <List className="w-5 h-5 mr-2" />
            View Approvals
          </Button>
          <Button variant="outline" size="lg" onClick={() => router.push('/plan')}>
            Create Another Workflow
          </Button>
        </section>
      </div>
    </main>
  )
}
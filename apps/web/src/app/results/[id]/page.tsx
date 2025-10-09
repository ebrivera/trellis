'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card } from '../../../components/ui/Card'
import { Button } from '../../../components/ui/Button'
import { Badge } from '../../../components/ui/Badge'
import { CheckCircle2, ArrowLeft, Users, MessageSquare, Mail, Phone, User, Lightbulb } from 'lucide-react'

interface Assignment {
  assigned_to: string
  assignment_type: string
  match_score: number
  status: string
}

interface Message {
  channel: string
  status: string
  template: string
  sent_at: string
}

interface AffectedPerson {
  id: string
  name: string
  email: string
  phone: string
  person_type: string
  assignments: Assignment[]
  messages: Message[]
}

interface WorkflowResult {
  id: string
  request: string
  template: string
  status: string
  winning_agent: string
  winning_strategy: string
  results: {
    assignments_created?: number
    notifications_sent?: number
    match_rate?: number
    avg_match_score?: number
    flagged_count?: number
    entities_analyzed?: number
    [key: string]: any
  }
  affected_people: AffectedPerson[]
  created_at: string
  completed_at: string
}

export default function ResultsPage() {
  const params = useParams()
  const router = useRouter()
  const [result, setResult] = useState<WorkflowResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchResult()
  }, [params.id])

  const fetchResult = async () => {
    try {
      setLoading(true)
      const response = await fetch(`http://localhost:8000/workflow/${params.id}`)

      if (!response.ok) {
        throw new Error('Failed to fetch workflow results')
      }

      const data = await response.json()

      // Parse assignments and messages if they're JSON strings
      if (data.affected_people) {
        data.affected_people = data.affected_people.map((person: any) => ({
          ...person,
          assignments: Array.isArray(person.assignments)
            ? person.assignments
            : (typeof person.assignments === 'string'
              ? JSON.parse(person.assignments)
              : []),
          messages: Array.isArray(person.messages)
            ? person.messages
            : (typeof person.messages === 'string'
              ? JSON.parse(person.messages)
              : [])
        }))
      }

      setResult(data)
    } catch (err) {
      console.error('Error fetching results:', err)
      setError('Could not load workflow results. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const getAgentInfo = (agentName: string) => {
    const agents: Record<string, { name: string; role: string; color: string; icon: string }> = {
      'planner': {
        name: 'Strategic Planner',
        role: 'Focused on maximizing coverage and optimizing metrics',
        color: 'text-blue-400',
        icon: '📊'
      },
      'operations': {
        name: 'Operations Manager',
        role: 'Focused on practical implementation and staff workload',
        color: 'text-green-400',
        icon: '⚙️'
      },
      'humanflourishing': {
        name: 'People & Relationships',
        role: 'Focused on personal connection and spiritual growth',
        color: 'text-purple-400',
        icon: '💜'
      }
    }

    const normalized = agentName.toLowerCase().replace(/\s+/g, '')
    return agents[normalized] || { name: agentName, role: 'AI Agent', color: 'text-white', icon: '🤖' }
  }

  const getTemplateLabel = (template: string) => {
    const labels: Record<string, string> = {
      'matching': 'Matching Workflow',
      'monitoring': 'Monitoring Workflow',
      'analysis': 'Analysis Workflow'
    }
    return labels[template] || template
  }

  const getHumanReadableSummary = (result: WorkflowResult) => {
    const peopleCount = result.affected_people?.length || 0
    if (result.template === 'matching') {
      return `Successfully matched ${peopleCount} ${peopleCount === 1 ? 'person' : 'people'} with a ${Math.round((result.results.match_rate || 0) * 100)}% match rate.`
    } else if (result.template === 'monitoring') {
      return `Identified ${peopleCount} ${peopleCount === 1 ? 'person' : 'people'} who need follow-up attention.`
    } else if (result.template === 'analysis') {
      const entitiesAnalyzed = result.results.entities_analyzed || 0
      const metricCount = result.results.metric_count || Object.keys(result.results.metrics || {}).length
      return `Analyzed ${entitiesAnalyzed} ${result.results.source_type || 'records'} and calculated ${metricCount} ${metricCount === 1 ? 'metric' : 'metrics'}.`
    }
    return `Workflow completed successfully, affecting ${peopleCount} ${peopleCount === 1 ? 'person' : 'people'}.`
  }

  const formatPhoneNumber = (phone: string | null) => {
    if (!phone) return 'No phone'
    return phone
  }

  if (loading) {
    return (
      <main className="min-h-screen px-6 pt-32 pb-20">
        <div className="max-w-6xl mx-auto text-center">
          <div className="flex items-center justify-center gap-2">
            <div className="w-2 h-2 bg-white rounded-full animate-bounce" />
            <div className="w-2 h-2 bg-white rounded-full animate-bounce [animation-delay:0.2s]" />
            <div className="w-2 h-2 bg-white rounded-full animate-bounce [animation-delay:0.4s]" />
          </div>
          <p className="mt-4 text-white/70">Loading results...</p>
        </div>
      </main>
    )
  }

  if (error || !result) {
    return (
      <main className="min-h-screen px-6 pt-32 pb-20">
        <div className="max-w-6xl mx-auto text-center">
          <p className="text-red-400">{error || 'Result not found'}</p>
          <Button onClick={() => router.push('/approvals')} variant="outline" className="mt-4">
            <ArrowLeft className="inline-block w-4 h-4 mr-2" />
            Back to Approvals
          </Button>
        </div>
      </main>
    )
  }

  const agent = getAgentInfo(result.winning_agent)

  return (
    <main className="min-h-screen px-6 pt-32 pb-20">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => router.push('/approvals')}
            className="mb-4"
          >
            <ArrowLeft className="inline-block w-4 h-4 mr-2" />
            Back to Approvals
          </Button>

          <div className="flex items-start justify-between gap-4 mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle2 className="w-8 h-8 text-green-400" />
                <h1 className="text-4xl font-bold text-white">
                  Workflow Complete!
                </h1>
              </div>
              <p className="text-lg text-white/70">{getHumanReadableSummary(result)}</p>
            </div>
            <Badge variant="success" className="px-4 py-2 text-lg shrink-0">
              Completed
            </Badge>
          </div>

          <p className="text-sm text-white/50">
            Completed {new Date(result.completed_at).toLocaleString()}
          </p>
        </div>

        {/* Your Request */}
        <section className="mb-8">
          <Card padding="lg">
            <h2 className="mb-3 text-xl font-semibold text-white">Your Request</h2>
            <p className="text-white/80">{result.request}</p>
            <div className="mt-3">
              <Badge variant="info">{getTemplateLabel(result.template)}</Badge>
            </div>
          </Card>
        </section>

        {/* Winning Strategy */}
        {result.winning_strategy && (
          <section className="mb-8">
            <Card padding="lg" className="border-2 border-white/20">
              <div className="flex items-start gap-4">
                <div className="flex items-center justify-center w-12 h-12 text-2xl rounded-full shrink-0 bg-white/10">
                  {agent.icon}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Lightbulb className="w-5 h-5 text-yellow-400" />
                    <h2 className="text-xl font-semibold text-white">
                      The Approach: {agent.name}
                    </h2>
                  </div>
                  <p className="mb-3 text-sm text-white/60">{agent.role}</p>
                  <div className="p-4 rounded-lg bg-white/5">
                    <p className="text-white whitespace-pre-wrap">{result.winning_strategy}</p>
                  </div>
                </div>
              </div>
            </Card>
          </section>
        )}

        {/* Analysis Metrics (for analysis workflows) */}
        {result.template === 'analysis' && result.results.metrics && (
          <section className="mb-8">
            <div className="flex items-center gap-3 mb-4">
              <Lightbulb className="w-6 h-6 text-yellow-400" />
              <h2 className="text-2xl font-semibold text-white">
                Analysis Results
              </h2>
            </div>
            <Card padding="lg">
              <div className="space-y-6">
                {Object.entries(result.results.metrics).map(([metricName, metricValue]) => (
                  <div key={metricName}>
                    <h3 className="mb-3 text-lg font-semibold text-white">
                      {metricName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </h3>
                    {typeof metricValue === 'object' && metricValue !== null && !Array.isArray(metricValue) ? (
                      // Grouped metric - show breakdown
                      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
                        {Object.entries(metricValue as Record<string, any>).map(([group, value]) => (
                          <div key={group} className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/10">
                            <span className="text-sm font-medium text-white/80">{group}</span>
                            <span className="text-xl font-bold text-white">{value}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      // Scalar metric - show single value
                      <div className="p-6 rounded-lg bg-white/5 border border-white/10">
                        <p className="text-4xl font-bold text-white">{String(metricValue)}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          </section>
        )}

        {/* People Affected (for matching/monitoring workflows) */}
        {result.template !== 'analysis' && (
          <section className="mb-8">
            <div className="flex items-center gap-3 mb-4">
              <Users className="w-6 h-6 text-blue-400" />
              <h2 className="text-2xl font-semibold text-white">
                People Affected ({result.affected_people?.length || 0})
              </h2>
            </div>

            {result.affected_people && result.affected_people.length > 0 ? (
            <div className="space-y-4">
              {result.affected_people.map((person) => (
                <Card key={person.id} padding="lg" className="hover:bg-white/15">
                  <div className="flex flex-col gap-4 md:flex-row md:items-start">
                    {/* Person Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start gap-3 mb-3">
                        <div className="flex items-center justify-center w-10 h-10 rounded-full shrink-0 bg-gradient-to-br from-blue-500 to-purple-600">
                          <User className="w-5 h-5 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-semibold text-white">{person.name}</h3>
                          <div className="flex flex-col gap-1 mt-1">
                            {person.email && (
                              <div className="flex items-center gap-2 text-sm text-white/70">
                                <Mail className="w-4 h-4 shrink-0" />
                                <span className="truncate">{person.email}</span>
                              </div>
                            )}
                            {person.phone && (
                              <div className="flex items-center gap-2 text-sm text-white/70">
                                <Phone className="w-4 h-4 shrink-0" />
                                <span>{formatPhoneNumber(person.phone)}</span>
                              </div>
                            )}
                          </div>
                          <Badge variant="default" className="mt-2 capitalize">
                            {person.person_type}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    {/* Actions Taken */}
                    <div className="flex-1">
                      <h4 className="mb-2 text-sm font-semibold text-white/60">What We Did:</h4>
                      <div className="space-y-2">
                        {/* Assignments */}
                        {person.assignments && Array.isArray(person.assignments) && person.assignments.filter(a => a && a.assigned_to).length > 0 && (
                          <>
                            {person.assignments.filter(a => a && a.assigned_to).map((assignment, idx) => (
                              <div key={idx} className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                                <div className="flex items-start justify-between gap-2">
                                  <div className="flex-1">
                                    <p className="text-sm font-medium text-white">
                                      ✓ Matched to {assignment.assigned_to}
                                    </p>
                                    {assignment.match_score && (
                                      <p className="mt-1 text-xs text-white/60">
                                        Match quality: {Math.round(assignment.match_score * 100)}%
                                      </p>
                                    )}
                                  </div>
                                  <Badge variant="success" className="shrink-0">
                                    {assignment.status}
                                  </Badge>
                                </div>
                              </div>
                            ))}
                          </>
                        )}

                        {/* Messages */}
                        {person.messages && Array.isArray(person.messages) && person.messages.filter(m => m && m.channel).length > 0 && (
                          <>
                            {person.messages.filter(m => m && m.channel).map((message, idx) => (
                              <div key={idx} className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                                <div className="flex items-start justify-between gap-2">
                                  <div className="flex-1">
                                    <p className="text-sm font-medium text-white">
                                      <MessageSquare className="inline w-4 h-4 mr-1" />
                                      Sent {message.channel} notification
                                    </p>
                                    {message.sent_at && (
                                      <p className="mt-1 text-xs text-white/60">
                                        {new Date(message.sent_at).toLocaleString()}
                                      </p>
                                    )}
                                  </div>
                                  <Badge
                                    variant={message.status === 'sent' ? 'success' : 'default'}
                                    className="shrink-0 capitalize"
                                  >
                                    {message.status}
                                  </Badge>
                                </div>
                              </div>
                            ))}
                          </>
                        )}

                        {/* Show message if no actions */}
                        {(!person.assignments || person.assignments.filter(a => a && a.assigned_to).length === 0) &&
                         (!person.messages || person.messages.filter(m => m && m.channel).length === 0) && (
                          <p className="text-sm text-white/50 italic">No actions recorded</p>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
            ) : (
              <Card padding="lg" className="text-center">
                <p className="text-white/60">No people were directly affected by this workflow.</p>
              </Card>
            )}
          </section>
        )}

        {/* Summary Stats */}
        <section className="mb-8">
          <h2 className="mb-4 text-2xl font-semibold text-white">Summary</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {result.template === 'analysis' ? (
              <>
                <Card padding="lg" className="text-center">
                  <Lightbulb className="w-8 h-8 mx-auto mb-2 text-yellow-400" />
                  <p className="mb-1 text-sm text-white/60">Records Analyzed</p>
                  <p className="text-3xl font-bold text-white">{result.results.entities_analyzed || 0}</p>
                </Card>
                <Card padding="lg" className="text-center">
                  <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-green-400" />
                  <p className="mb-1 text-sm text-white/60">Metrics Calculated</p>
                  <p className="text-3xl font-bold text-white">{result.results.metric_count || 0}</p>
                </Card>
                <Card padding="lg" className="text-center">
                  <Users className="w-8 h-8 mx-auto mb-2 text-blue-400" />
                  <p className="mb-1 text-sm text-white/60">Data Source</p>
                  <p className="text-xl font-bold text-white capitalize">{result.results.source_type || 'Unknown'}</p>
                </Card>
              </>
            ) : (
              <>
                <Card padding="lg" className="text-center">
                  <Users className="w-8 h-8 mx-auto mb-2 text-blue-400" />
                  <p className="mb-1 text-sm text-white/60">Total People</p>
                  <p className="text-3xl font-bold text-white">{result.affected_people?.length || 0}</p>
                </Card>
                {result.results.assignments_created !== undefined && (
                  <Card padding="lg" className="text-center">
                    <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-green-400" />
                    <p className="mb-1 text-sm text-white/60">Matches Created</p>
                    <p className="text-3xl font-bold text-white">{result.results.assignments_created}</p>
                  </Card>
                )}
                {result.results.notifications_sent !== undefined && (
                  <Card padding="lg" className="text-center">
                    <MessageSquare className="w-8 h-8 mx-auto mb-2 text-purple-400" />
                    <p className="mb-1 text-sm text-white/60">Notifications Sent</p>
                    <p className="text-3xl font-bold text-white">{result.results.notifications_sent}</p>
                  </Card>
                )}
              </>
            )}
          </div>
        </section>

        {/* Actions */}
        <section className="flex flex-wrap gap-3">
          <Button size="lg" onClick={() => router.push('/plan')}>
            Create Another Workflow
          </Button>
          <Button variant="outline" size="lg" onClick={() => router.push('/approvals')}>
            View Approvals
          </Button>
        </section>
      </div>
    </main>
  )
}

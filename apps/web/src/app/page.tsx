'use client'

import Link from 'next/link'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Clock, BarChart3, MessageSquare, Users, Plus, CheckCircle2, Download, Target, Upload, XCircle } from 'lucide-react'
import { useState, useEffect } from 'react'

interface OverviewData {
  card1: { label: string; value: number }
  card2: { label: string; sublabel: string; value: number }
  card3: { label: string; value: number }
  card4: {
    label: string
    stats: Array<{ label: string; value: number }>
  }
}

interface Activity {
  activity_type: string
  id: string
  template_type: string
  status: string
  request_text: string
  created_at: string
  completed_at: string | null
}

interface RecentActivityData {
  activities: Activity[]
}

interface MonthlyMetric {
  label: string
  current: number
  previous: number
  change: number
}

interface MonthlyMetricsData {
  metrics: MonthlyMetric[]
}

export default function Dashboard() {
  const [overviewData, setOverviewData] = useState<OverviewData | null>(null)
  const [recentActivity, setRecentActivity] = useState<RecentActivityData | null>(null)
  const [monthlyMetrics, setMonthlyMetrics] = useState<MonthlyMetricsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activityLoading, setActivityLoading] = useState(true)
  const [metricsLoading, setMetricsLoading] = useState(true)

  useEffect(() => {
    const fetchOverview = async () => {
      try {
        const response = await fetch('http://localhost:8000/dashboard/overview')
        const data = await response.json()
        setOverviewData(data)
      } catch (error) {
        console.error('Failed to fetch overview data:', error)
      } finally {
        setLoading(false)
      }
    }

    const fetchRecentActivity = async () => {
      try {
        const response = await fetch('http://localhost:8000/dashboard/recent-activity')
        const data = await response.json()
        setRecentActivity(data)
      } catch (error) {
        console.error('Failed to fetch recent activity:', error)
      } finally {
        setActivityLoading(false)
      }
    }

    const fetchMonthlyMetrics = async () => {
      try {
        const response = await fetch('http://localhost:8000/dashboard/monthly-metrics')
        const data = await response.json()
        setMonthlyMetrics(data)
      } catch (error) {
        console.error('Failed to fetch monthly metrics:', error)
      } finally {
        setMetricsLoading(false)
      }
    }

    fetchOverview()
    fetchRecentActivity()
    fetchMonthlyMetrics()
  }, [])

  const getActivityIcon = (activity: Activity) => {
    if (activity.status === 'completed') {
      return <CheckCircle2 className="w-6 h-6 text-green-400" />
    } else if (activity.status === 'pending' || activity.status === 'awaiting_approval') {
      return <Clock className="w-6 h-6 text-yellow-400" />
    } else if (activity.status === 'rejected' || activity.status === 'failed') {
      return <XCircle className="w-6 h-6 text-red-400" />
    } else if (activity.activity_type === 'workflow') {
      return <BarChart3 className="w-6 h-6 text-blue-400" />
    } else {
      return <Target className="w-6 h-6 text-purple-400" />
    }
  }

  const getActivityTitle = (activity: Activity) => {
    const typeLabel = activity.activity_type === 'workflow' ? 'Workflow' : 'Approval'
    const statusLabel = activity.status === 'pending' ? ' (Pending)' : 
                       activity.status === 'awaiting_approval' ? ' (Awaiting Approval)' :
                       activity.status === 'completed' ? ' Completed' :
                       activity.status === 'rejected' ? ' Rejected' : ''
    
    const requestPreview = activity.request_text?.slice(0, 50) || activity.template_type
    return `${typeLabel}${statusLabel}: ${requestPreview}${activity.request_text?.length > 50 ? '...' : ''}`
  }

  const getTimeAgo = (timestamp: string) => {
    const now = new Date()
    const then = new Date(timestamp)
    const diffMs = now.getTime() - then.getTime()
    
    // Handle future timestamps (shouldn't happen but just in case)
    if (diffMs < 0) return 'just now'
    
    const diffSecs = Math.floor(diffMs / 1000)
    const diffMins = Math.floor(diffSecs / 60)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffSecs < 10) return 'just now'
    if (diffSecs < 60) return `${diffSecs} seconds ago`
    if (diffMins === 1) return '1 minute ago'
    if (diffMins < 60) return `${diffMins} minutes ago`
    if (diffHours === 1) return '1 hour ago'
    if (diffHours < 24) return `${diffHours} hours ago`
    if (diffDays === 1) return '1 day ago'
    return `${diffDays} days ago`
  }

  return (
    <main className="min-h-screen px-6 pt-32 pb-20">
      <div className="mx-auto max-w-7xl">
        {/* Header / Hero Section */}
        <section className="mb-12">
          <h1 className="mb-2 text-5xl font-bold text-white">
            Welcome back, Pastor John
          </h1>
          <p className="mb-6 text-lg text-white/70">
            Turn your data into ministry outcomes, safely and simply.
          </p>
          <Link href="/plan">
            <Button size="lg" className="shadow-xl">
              <Plus className="inline-block w-5 h-5 mr-2" />
              Start New Goal
            </Button>
          </Link>
        </section>

        {/* Summary Cards */}
        <section className="mb-12">
          <h2 className="mb-6 text-2xl font-semibold text-white">Overview</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
            {/* Card 1: Pending Approvals */}
            <Card padding="lg" className="transition-all duration-300 hover:scale-105 hover:shadow-[0_0_30px_rgba(255,255,255,0.3)]">
              <div className="flex flex-col gap-2">
                <Clock className="w-10 h-10 text-white" />
                <h3 className="text-lg font-semibold text-white">
                  {loading ? 'Loading...' : overviewData?.card1.label || 'Pending Approvals'}
                </h3>
                <p className="text-3xl font-bold text-white">
                  {loading ? '...' : overviewData?.card1.value ?? 0}
                </p>
                <p className="text-sm text-white/60">awaiting your review</p>
                <Link href="/approvals" className="mt-2">
                  <Button variant="ghost" size="sm" className="w-full">
                    Review →
                  </Button>
                </Link>
              </div>
            </Card>

            {/* Card 2: Completed Workflows */}
            <Card padding="lg" className="transition-all duration-300 hover:scale-105 hover:shadow-[0_0_30px_rgba(255,255,255,0.3)]">
              <div className="flex flex-col gap-2">
                <BarChart3 className="w-10 h-10 text-white" />
                <h3 className="text-lg font-semibold text-white">
                  {loading ? 'Loading...' : overviewData?.card2.label || 'Completed Workflows'}
                </h3>
                <p className="text-3xl font-bold text-white">
                  {loading ? '...' : overviewData?.card2.value ?? 0}
                </p>
                <p className="text-sm text-white/60">
                  {overviewData?.card2.sublabel || 'Last 7 Days'}
                </p>
              </div>
            </Card>

            {/* Card 3: Messages Queued */}
            <Card padding="lg" className="transition-all duration-300 hover:scale-105 hover:shadow-[0_0_30px_rgba(255,255,255,0.3)]">
              <div className="flex flex-col gap-2">
                <MessageSquare className="w-10 h-10 text-white" />
                <h3 className="text-lg font-semibold text-white">
                  {loading ? 'Loading...' : overviewData?.card3.label || 'Messages Queued'}
                </h3>
                <p className="text-3xl font-bold text-white">
                  {loading ? '...' : overviewData?.card3.value ?? 0}
                </p>
                <p className="text-sm text-white/60">pending delivery</p>
              </div>
            </Card>

            {/* Card 4: Statistics */}
            <Card padding="lg" className="transition-all duration-300 hover:scale-105 hover:shadow-[0_0_30px_rgba(255,255,255,0.3)]">
              <div className="flex flex-col gap-2">
                <Users className="w-10 h-10 text-white" />
                <h3 className="text-lg font-semibold text-white">
                  {loading ? 'Loading...' : overviewData?.card4.label || 'Statistics'}
                </h3>
                <div className="mt-2 space-y-2">
                  {loading ? (
                    <div className="text-white/60">Loading...</div>
                  ) : (
                    overviewData?.card4.stats.map((stat, index) => (
                      <div key={index} className="flex justify-between">
                        <span className="text-white/60">{stat.label}</span>
                        <span className="font-bold text-white">{stat.value}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </Card>
          </div>
        </section>

        {/* Recent Activity Feed */}
        <section className="mb-12">
          <h2 className="mb-6 text-2xl font-semibold text-white">
            Recent Activity
          </h2>
          <Card>  {/* Remove className="space-y-4" */}
            {activityLoading ? (
              <div className="py-8 text-center text-white/60">Loading activities...</div>
            ) : recentActivity?.activities && recentActivity.activities.length > 0 ? (
              recentActivity.activities.map((activity, index) => (
                <div key={activity.id}>
                  {index > 0 && <Divider />}
                  <div className="py-4">  {/* Add padding wrapper */}
                    <ActivityItem
                      icon={getActivityIcon(activity)}
                      title={getActivityTitle(activity)}
                      time={getTimeAgo(activity.created_at)}
                      action={
                        activity.status === 'pending' || activity.status === 'awaiting_approval' ? (
                          <Link href="/approvals">
                            <Button variant="ghost" size="sm">
                              Review
                            </Button>
                          </Link>
                        ) : undefined
                      }
                    />
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-white/60">No recent activity</div>
            )}
          </Card>
        </section>

        {/* Quick Actions */}
        <section className="mb-12">
          <h2 className="mb-6 text-2xl font-semibold text-white">Quick Actions</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Link href="/settings" className="block">
              <Button variant="outline" size="lg" className="justify-center w-full">
                <Upload className="inline-block w-5 h-5 mr-2" />
                Import Data
              </Button>
            </Link>
            <Link href="/plan" className="block">
              <Button variant="outline" size="lg" className="justify-center w-full">
                <Plus className="inline-block w-5 h-5 mr-2" />
                Start New Goal
              </Button>
            </Link>
            <Link href="/approvals" className="block">
              <Button variant="outline" size="lg" className="justify-center w-full">
                <CheckCircle2 className="inline-block w-5 h-5 mr-2" />
                Review Approvals
              </Button>
            </Link>
            <Button variant="outline" size="lg" className="justify-center">
              <BarChart3 className="inline-block w-5 h-5 mr-2" />
              View Reports
            </Button>
          </div>
        </section>

        {/* Metrics Snapshot */}
        <section>
          <h2 className="mb-6 text-2xl font-semibold text-white">This Month</h2>
          <Card>
            {metricsLoading ? (
              <div className="py-8 text-center text-white/60">Loading metrics...</div>
            ) : (
              <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
                {(monthlyMetrics?.metrics || []).map((metric, index) => (
                  <MetricItem
                    key={index}
                    label={metric.label}
                    value={metric.current.toString()}
                    change={`${metric.change >= 0 ? '+' : ''}${metric.change} from last month`}
                    trend={metric.change >= 0 ? 'up' : 'down'}
                  />
                ))}
              </div>
            )}
          </Card>
        </section>
      </div>
    </main>
  )
}

function ActivityItem({
  icon,
  title,
  time,
  action,
}: {
  icon: React.ReactNode
  title: string
  time: string
  action?: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="shrink-0">{icon}</div>  {/* Removed mt-1 */}
        <div>
          <p className="font-medium text-white">{title}</p>
          <p className="text-sm text-white/50">{time}</p>
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  )
}

function Divider() {
  return <div className="w-full h-px bg-white/10" />
}

function MetricItem({
  label,
  value,
  change,
  trend,
}: {
  label: string
  value: string
  change: string
  trend: 'up' | 'down'
}) {
  return (
    <div className="text-center">
      <p className="mb-2 text-sm font-medium text-white/60">{label}</p>
      <p className="mb-1 text-4xl font-bold text-white">{value}</p>
      <p
        className={`text-sm ${
          trend === 'up' ? 'text-green-400' : 'text-red-400'
        }`}
      >
        {change}
      </p>
    </div>
  )
}
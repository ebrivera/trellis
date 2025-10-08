'use client'

import Link from 'next/link'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Clock, BarChart3, MessageSquare, Users, Plus, CheckCircle2, Download, Target, Upload } from 'lucide-react'
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

export default function Dashboard() {
  const [overviewData, setOverviewData] = useState<OverviewData | null>(null)
  const [loading, setLoading] = useState(true)

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

    fetchOverview()
  }, [])

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
            <Card padding="lg" className="transition-transform hover:scale-105">
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
            <Card padding="lg" className="transition-transform hover:scale-105">
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
            <Card padding="lg" className="transition-transform hover:scale-105">
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
            <Card padding="lg" className="transition-transform hover:scale-105">
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
          <Card className="space-y-4">
            <ActivityItem
              icon={<CheckCircle2 className="w-6 h-6 text-green-400" />}
              title="Activity 1"
              time="2 hours ago"
            />
            <Divider />
            <ActivityItem
              icon={<Clock className="w-6 h-6 text-yellow-400" />}
              title="Activity 2 (Pending Approval)"
              time="5 hours ago"
              action={
                <Link href="/approvals">
                  <Button variant="ghost" size="sm">
                    Review
                  </Button>
                </Link>
              }
            />
            <Divider />
            <ActivityItem
              icon={<BarChart3 className="w-6 h-6 text-blue-400" />}
              title="Activity 3"
              time="1 day ago"
            />
            <Divider />
            <ActivityItem
              icon={<Download className="w-6 h-6 text-purple-400" />}
              title="Activity 4"
              time="2 days ago"
            />
            <Divider />
            <ActivityItem
              icon={<Target className="w-6 h-6 text-pink-400" />}
              title="Activity 5"
              time="3 days ago"
            />
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
            <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
              <MetricItem
                label="Metric 1"
                value="3"
                change="+2 from last month"
                trend="up"
              />
              <MetricItem
                label="Metric 2"
                value="52"
                change="+18 from last month"
                trend="up"
              />
              <MetricItem
                label="Metric 3"
                value="847"
                change="+124 from last month"
                trend="up"
              />
            </div>
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
    <div className="flex items-start justify-between gap-4">
      <div className="flex items-start gap-3">
        <div className="mt-1 shrink-0">{icon}</div>
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
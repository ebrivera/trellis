import Link from 'next/link'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'

export default function Dashboard() {
  return (
    <main className="min-h-screen px-6 pt-32 pb-20">
      <div className="mx-auto max-w-7xl">
        {/* Header / Hero Section */}
        <section className="mb-12">
          <h1 className="mb-2 text-5xl font-bold text-white">
            Welcome back, Pastor John 👋
          </h1>
          <p className="mb-6 text-lg text-white/70">
            Turn your data into ministry outcomes, safely and simply.
          </p>
          <Link href="/goals">
            <Button size="lg" className="shadow-xl">
              ➕ Start New Goal
            </Button>
          </Link>
        </section>

        {/* Summary Cards */}
        <section className="mb-12">
          <h2 className="mb-6 text-2xl font-semibold text-white">Overview</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Card padding="lg" className="transition-transform hover:scale-105">
              <div className="flex flex-col gap-2">
                <div className="text-4xl">⏳</div>
                <h3 className="text-lg font-semibold text-white">
                  Pending Approvals
                </h3>
                <p className="text-3xl font-bold text-white">2</p>
                <p className="text-sm text-white/60">awaiting your review</p>
                <Link href="/approvals" className="mt-2">
                  <Button variant="ghost" size="sm" className="w-full">
                    Review →
                  </Button>
                </Link>
              </div>
            </Card>

            <Card padding="lg" className="transition-transform hover:scale-105">
              <div className="flex flex-col gap-2">
                <div className="text-4xl">📊</div>
                <h3 className="text-lg font-semibold text-white">
                  Recent Workflows
                </h3>
                <p className="text-xl font-bold text-white">Scheduled Plan</p>
                <p className="text-sm text-white/60">3 of 4 steps completed</p>
                <div className="w-full h-2 mt-2 rounded-full bg-white/20">
                  <div className="w-3/4 h-2 bg-white rounded-full" />
                </div>
              </div>
            </Card>

            <Card padding="lg" className="transition-transform hover:scale-105">
              <div className="flex flex-col gap-2">
                <div className="text-4xl">💬</div>
                <h3 className="text-lg font-semibold text-white">
                  Task Scheduled
                </h3>
                <p className="text-3xl font-bold text-white">125</p>
                <p className="text-sm text-white/60">87% delivered</p>
                <div className="flex gap-2 mt-2">
                  <div className="flex-1 text-center">
                    <div className="text-xl font-bold text-green-400">109</div>
                    <div className="text-xs text-white/50">sent</div>
                  </div>
                  <div className="flex-1 text-center">
                    <div className="text-xl font-bold text-yellow-400">16</div>
                    <div className="text-xs text-white/50">pending</div>
                  </div>
                </div>
              </div>
            </Card>

            <Card padding="lg" className="transition-transform hover:scale-105">
              <div className="flex flex-col gap-2">
                <div className="text-4xl">👥</div>
                <h3 className="text-lg font-semibold text-white">
                  Statistics
                </h3>
                <div className="mt-2 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-white/60">Statistic 1</span>
                    <span className="font-bold text-white">245</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/60">Statistic 2</span>
                    <span className="font-bold text-white">8</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/60">Statistic 3</span>
                    <span className="font-bold text-white">2</span>
                  </div>
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
              icon="✔️"
              title="Activity 1"
              time="2 hours ago"
            />
            <Divider />
            <ActivityItem
              icon="⏳"
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
              icon="📊"
              title="Activity 3"
              time="1 day ago"
            />
            <Divider />
            <ActivityItem
              icon="📥"
              title="Activity 4"
              time="2 days ago"
            />
            <Divider />
            <ActivityItem
              icon="🎯"
              title="Activity 5"
              time="3 days ago"
            />
          </Card>
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
  icon: string
  title: string
  time: string
  action?: React.ReactNode
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div className="flex items-start gap-3">
        <span className="text-2xl">{icon}</span>
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

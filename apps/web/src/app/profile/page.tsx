import { Card } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { User, Mail, Briefcase, Calendar, MapPin } from 'lucide-react'

export default function ProfilePage() {
  return (
    <main className="min-h-screen px-6 pt-32 pb-20">
      <div className="w-full max-w-3xl mx-auto">
        {/* Header */}
        <header className="mb-8">
          <h1 className="mb-2 text-4xl font-bold text-white">Profile</h1>
          <p className="text-lg text-white/70">
            Your account information and details.
          </p>
        </header>

        {/* Profile Card */}
        <Card padding="lg">
          <div className="flex flex-col items-center gap-6 pb-6 mb-6 border-b border-white/10">
            {/* Avatar */}
            <div className="flex items-center justify-center w-24 h-24 text-3xl font-bold text-white rounded-full bg-gradient-to-br from-blue-500 to-purple-600">
              JD
            </div>

            {/* Name & Role */}
            <div className="text-center">
              <h2 className="mb-2 text-2xl font-bold text-white">Pastor John Doe</h2>
              <Badge variant="info">Lead Pastor</Badge>
            </div>
          </div>

          {/* Details */}
          <div className="space-y-4">
            <ProfileDetail
              icon={<Mail className="w-5 h-5 text-white/60" />}
              label="Email"
              value="john@church.org"
            />
            <ProfileDetail
              icon={<Briefcase className="w-5 h-5 text-white/60" />}
              label="Department"
              value="Leadership & Administration"
            />
            <ProfileDetail
              icon={<Calendar className="w-5 h-5 text-white/60" />}
              label="Member Since"
              value="January 2020"
            />
            <ProfileDetail
              icon={<MapPin className="w-5 h-5 text-white/60" />}
              label="Location"
              value="Los Angeles, CA"
            />
          </div>
        </Card>

        {/* Stats Card */}
        <Card padding="lg" className="mt-6">
          <h3 className="mb-4 text-xl font-semibold text-white">Activity Summary</h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <StatItem label="Plans Created" value="12" />
            <StatItem label="Approvals Given" value="48" />
            <StatItem label="Messages Sent" value="1,247" />
          </div>
        </Card>
      </div>
    </main>
  )
}

function ProfileDetail({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div className="flex items-start gap-3 pb-4 border-b border-white/10 last:border-0">
      {icon}
      <div className="flex-1">
        <p className="text-sm font-medium text-white/60">{label}</p>
        <p className="text-lg text-white">{value}</p>
      </div>
    </div>
  )
}

function StatItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-4 text-center transition-colors rounded-lg bg-white/5 hover:bg-white/10">
      <p className="mb-1 text-3xl font-bold text-white">{value}</p>
      <p className="text-sm text-white/60">{label}</p>
    </div>
  )
}


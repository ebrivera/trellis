import { ReactNode } from 'react'

interface PlanCardProps {
  icon: string
  title: string
  description: string
}

export function PlanCard({ icon, title, description }: PlanCardProps) {
  return (
    <div className="flex items-start gap-3 p-4 transition-colors rounded-2xl bg-white/5 hover:bg-white/10">
      <span className="text-2xl shrink-0">{icon}</span>
      <div className="flex-1">
        <h4 className="mb-1 font-semibold text-white">{title}</h4>
        <p className="text-sm text-white/70">{description}</p>
      </div>
    </div>
  )
}

export default PlanCard


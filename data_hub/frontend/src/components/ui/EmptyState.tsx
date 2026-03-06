import type { ReactNode } from 'react'
import { Inbox } from 'lucide-react'

interface Props {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
}

export default function EmptyState({ icon, title, description, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-12 h-12 rounded-full bg-hub-muted flex items-center justify-center mb-4 text-hub-text-muted">
        {icon ?? <Inbox size={22} />}
      </div>
      <h3 className="text-sm font-semibold text-hub-text-primary mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-hub-text-muted max-w-xs leading-relaxed">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

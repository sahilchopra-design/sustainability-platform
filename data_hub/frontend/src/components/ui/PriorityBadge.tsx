import { clsx } from 'clsx'
import type { Priority } from '@/types'

const config = {
  P0: { bg: 'bg-hub-error/15', text: 'text-hub-error', border: 'border-hub-error/30' },
  P1: { bg: 'bg-hub-warning/15', text: 'text-hub-warning', border: 'border-hub-warning/30' },
  P2: { bg: 'bg-hub-muted', text: 'text-hub-text-secondary', border: 'border-hub-border' },
}

interface Props {
  priority: Priority | string
  showLabel?: boolean
}

export default function PriorityBadge({ priority, showLabel = false }: Props) {
  const c = config[priority as Priority] ?? config.P2
  return (
    <span className={clsx(
      'inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold border',
      c.bg, c.text, c.border,
    )}>
      {priority}
      {showLabel && (
        <span className="font-normal opacity-70">
          {priority === 'P0' ? '— Critical' : priority === 'P1' ? '— High' : '— Backlog'}
        </span>
      )}
    </span>
  )
}

import { clsx } from 'clsx'
import type { Utility } from '@/types'

const config = {
  benchmarking: { label: 'Benchmarking', bg: 'bg-hub-secondary/15', text: 'text-hub-secondary', icon: '▲' },
  referencing:  { label: 'Referencing',  bg: 'bg-hub-accent/15',    text: 'text-hub-accent',    icon: '◆' },
  approximation:{ label: 'Approximation',bg: 'bg-hub-warning/15',   text: 'text-hub-warning',   icon: '≈' },
  supplementary:{ label: 'Supplementary',bg: 'bg-hub-muted',        text: 'text-hub-text-secondary', icon: '+' },
}

interface Props {
  utility: Utility | string
  compact?: boolean
}

export default function UtilityBadge({ utility, compact = false }: Props) {
  const c = config[utility as Utility] ?? config.supplementary
  return (
    <span className={clsx(
      'inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-medium',
      c.bg, c.text,
    )}>
      <span className="opacity-70 text-[9px]">{c.icon}</span>
      {compact ? utility : c.label}
    </span>
  )
}

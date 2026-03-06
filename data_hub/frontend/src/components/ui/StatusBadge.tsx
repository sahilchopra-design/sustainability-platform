import { clsx } from 'clsx'
import type { SourceStatus, SyncStatus } from '@/types'

type Status = SourceStatus | SyncStatus | string

const config: Record<string, { label: string; dot: string; bg: string; text: string }> = {
  active:      { label: 'Active',      dot: 'bg-hub-success', bg: 'bg-hub-success/10', text: 'text-hub-success' },
  configuring: { label: 'Configuring', dot: 'bg-hub-accent',  bg: 'bg-hub-accent/10',  text: 'text-hub-accent' },
  planned:     { label: 'Planned',     dot: 'bg-hub-text-muted', bg: 'bg-hub-muted',   text: 'text-hub-text-secondary' },
  paused:      { label: 'Paused',      dot: 'bg-hub-warning', bg: 'bg-hub-warning/10', text: 'text-hub-warning' },
  error:       { label: 'Error',       dot: 'bg-hub-error',   bg: 'bg-hub-error/10',   text: 'text-hub-error' },
  pending:     { label: 'Pending',     dot: 'bg-hub-text-muted', bg: 'bg-hub-muted',   text: 'text-hub-text-secondary' },
  running:     { label: 'Running',     dot: 'bg-hub-accent animate-pulse',  bg: 'bg-hub-accent/10',  text: 'text-hub-accent' },
  success:     { label: 'Success',     dot: 'bg-hub-success', bg: 'bg-hub-success/10', text: 'text-hub-success' },
  failed:      { label: 'Failed',      dot: 'bg-hub-error',   bg: 'bg-hub-error/10',   text: 'text-hub-error' },
  skipped:     { label: 'Skipped',     dot: 'bg-hub-warning', bg: 'bg-hub-warning/10', text: 'text-hub-warning' },
}

interface Props {
  status: Status
  size?: 'sm' | 'md'
}

export default function StatusBadge({ status, size = 'sm' }: Props) {
  const c = config[status] ?? { label: status, dot: 'bg-hub-text-muted', bg: 'bg-hub-muted', text: 'text-hub-text-secondary' }
  return (
    <span className={clsx(
      'inline-flex items-center gap-1.5 rounded-full font-medium',
      c.bg, c.text,
      size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs',
    )}>
      <span className={clsx('rounded-full flex-shrink-0', c.dot, size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2')} />
      {c.label}
    </span>
  )
}

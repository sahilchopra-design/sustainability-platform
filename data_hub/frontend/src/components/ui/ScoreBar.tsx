import { clsx } from 'clsx'

interface Props {
  score: number
  max?: number
  label?: string
  showValue?: boolean
  size?: 'sm' | 'md'
  className?: string
}

function scoreColor(pct: number): string {
  if (pct >= 72) return 'bg-hub-success'
  if (pct >= 50) return 'bg-hub-warning'
  return 'bg-hub-error'
}

export default function ScoreBar({ score, max = 100, label, showValue = true, size = 'sm', className }: Props) {
  const pct = Math.min(100, Math.round((score / max) * 100))
  return (
    <div className={clsx('flex flex-col gap-1', className)}>
      {(label || showValue) && (
        <div className="flex items-center justify-between">
          {label && <span className="text-[11px] text-hub-text-muted">{label}</span>}
          {showValue && (
            <span className="text-[11px] font-mono font-medium text-hub-text-secondary ml-auto">
              {score.toFixed(0)}<span className="text-hub-text-muted">/{max}</span>
            </span>
          )}
        </div>
      )}
      <div className={clsx('w-full bg-hub-muted rounded-full overflow-hidden', size === 'sm' ? 'h-1.5' : 'h-2')}>
        <div
          className={clsx('h-full rounded-full transition-all duration-500', scoreColor(pct))}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

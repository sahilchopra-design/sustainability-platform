import { clsx } from 'clsx'

interface Props {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export default function Spinner({ size = 'md', className }: Props) {
  const s = { sm: 'w-4 h-4 border-2', md: 'w-6 h-6 border-2', lg: 'w-8 h-8 border-[3px]' }[size]
  return (
    <div
      className={clsx(
        'rounded-full border-hub-muted border-t-hub-primary animate-spin',
        s,
        className,
      )}
    />
  )
}

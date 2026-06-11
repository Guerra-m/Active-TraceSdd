interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
}

export function Spinner({ size = 'md' }: SpinnerProps) {
  return (
    <div
      role="status"
      aria-label="Cargando"
      className={`animate-spin rounded-full border-2 border-brand-200 border-t-brand-600 ${sizeClasses[size]}`}
    />
  )
}
